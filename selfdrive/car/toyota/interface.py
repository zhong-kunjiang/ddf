#!/usr/bin/env python
import os
import time
import common.numpy_fast as np
from selfdrive.config import Conversions as CV
from selfdrive.car.toyota.carstate import CarState, CAR
from selfdrive.car.toyota.carcontroller import CarController, ECU, check_ecu_msgs
from cereal import car
from selfdrive.services import service_list
import selfdrive.messaging as messaging
from selfdrive.controls.lib.drive_helpers import EventTypes as ET, create_event


class CarInterface(object):
  def __init__(self, CP, logcan, sendcan=None):
    self.logcan = logcan
    self.CP = CP

    self.frame = 0
    self.can_invalid_count = 0
    self.gas_pressed_prev = False
    self.brake_pressed_prev = False
    self.cruise_enabled_prev = False

    # *** init the major players ***
    self.CS = CarState(CP, self.logcan)

    # sending if read only is False
    if sendcan is not None:
      self.sendcan = sendcan
      self.CC = CarController(CP.carFingerprint, CP.enableCamera, CP.enableDsu, CP.enableApgs)

  @staticmethod
  def get_params(candidate, fingerprint):

    # kg of standard extra cargo to count for drive, gas, etc...
    std_cargo = 136

    ret = car.CarParams.new_message()

    ret.carName = "toyota"
    ret.radarName = "toyota"
    ret.carFingerprint = candidate

    ret.safetyModel = car.CarParams.SafetyModels.toyota

    ret.enableSteer = True
    ret.enableBrake = True

    # pedal
    ret.enableCruise = True

    # FIXME: hardcoding honda civic 2016 touring params so they can be used to
    # scale unknown params for other cars
    m_civic = 2923./2.205 + std_cargo
    l_civic = 2.70
    aF_civic = l_civic * 0.4
    aR_civic = l_civic - aF_civic
    j_civic = 2500
    cF_civic = 85400
    cR_civic = 90000

    stop_and_go = True
    ret.m = 3045./2.205 + std_cargo
    ret.l = 2.70
    ret.aF = ret.l * 0.44
    ret.sR = 14.5 #Rav4 2017, TODO: find exact value for Prius
    ret.steerKp, ret.steerKi = 0.6, 0.05
    ret.steerKf = 0.00006   # full torque for 10 deg at 80mph means 0.00007818594

    ret.longPidDeadzoneBP = [0., 9.]
    ret.longPidDeadzoneV = [0., .15]

    # min speed to enable ACC. if car can do stop and go, then set enabling speed
    # to a negative value, so it won't matter.
    if candidate == CAR.PRIUS:
      ret.minEnableSpeed = -1.
    elif candidate == CAR.RAV4:   # TODO: hack Rav4 to do stop and go
      ret.minEnableSpeed = 19. * CV.MPH_TO_MS

    ret.aR = ret.l - ret.aF
    # TODO: get actual value, for now starting with reasonable value for
    # civic and scaling by mass and wheelbase
    ret.j = j_civic * ret.m * ret.l**2 / (m_civic * l_civic**2)

    # TODO: start from empirically derived lateral slip stiffness for the civic and scale by
    # mass and CG position, so all cars will have approximately similar dyn behaviors
    ret.cF = cF_civic * ret.m / m_civic * (ret.aR / ret.l) / (aR_civic / l_civic)
    ret.cR = cR_civic * ret.m / m_civic * (ret.aF / ret.l) / (aF_civic / l_civic)

    # no rear steering, at least on the listed cars above
    ret.chi = 0.

    # steer, gas, brake limitations VS speed
    ret.steerMaxBP = [16. * CV.KPH_TO_MS, 45. * CV.KPH_TO_MS]  # breakpoints at 1 and 40 kph
    ret.steerMaxV = [1., 1.]  # 2/3rd torque allowed above 45 kph
    ret.gasMaxBP = [0.]
    ret.gasMaxV = [0.5]
    ret.brakeMaxBP = [5., 20.]
    ret.brakeMaxV = [1., 0.8]

    ret.enableCamera = not check_ecu_msgs(fingerprint, candidate, ECU.CAM)
    ret.enableDsu = not check_ecu_msgs(fingerprint, candidate, ECU.DSU)
    ret.enableApgs = False # not check_ecu_msgs(fingerprint, candidate, ECU.APGS)
    print "ECU Camera Simulated: ", ret.enableCamera
    print "ECU DSU Simulated: ", ret.enableDsu
    print "ECU APGS Simulated: ", ret.enableApgs
    ret.enableGas = True

    ret.steerLimitAlert = False

    return ret

  @staticmethod
  def compute_gb(accel, speed):
    # toyota interface is already in accelration cmd, so conversion to gas-brake it's a pass-through.
    return accel

  # returns a car.CarState
  def update(self, c):
    # ******************* do can recv *******************
    can_pub_main = []
    canMonoTimes = []

    self.CS.update()

    # create message
    ret = car.CarState.new_message()

    # speeds
    ret.vEgo = self.CS.v_ego
    ret.vEgoRaw = self.CS.v_ego_raw
    ret.aEgo = self.CS.a_ego
    ret.standstill = self.CS.standstill
    ret.wheelSpeeds.fl = self.CS.v_wheel_fl
    ret.wheelSpeeds.fr = self.CS.v_wheel_fr
    ret.wheelSpeeds.rl = self.CS.v_wheel_rl
    ret.wheelSpeeds.rr = self.CS.v_wheel_rr

    # gear shifter
    ret.gearShifter = self.CS.gear_shifter

    # gas pedal
    ret.gas = self.CS.car_gas / 256.0
    ret.gasPressed = self.CS.pedal_gas > 0

    # brake pedal
    ret.brake = self.CS.user_brake
    ret.brakePressed = self.CS.brake_pressed != 0

    # steering wheel
    ret.steeringAngle = self.CS.angle_steers
    ret.steeringRate = self.CS.angle_steers_rate

    ret.steeringTorque = 0
    ret.steeringPressed = self.CS.steer_override

    # cruise state
    ret.cruiseState.enabled = self.CS.pcm_acc_status != 0
    ret.cruiseState.speed = self.CS.v_cruise_pcm * CV.KPH_TO_MS
    ret.cruiseState.available = bool(self.CS.main_on)
    ret.cruiseState.speedOffset = 0.

    # TODO: button presses
    buttonEvents = []

    if self.CS.left_blinker_on != self.CS.prev_left_blinker_on:
      be = car.CarState.ButtonEvent.new_message()
      be.type = 'leftBlinker'
      be.pressed = self.CS.left_blinker_on != 0
      buttonEvents.append(be)

    if self.CS.right_blinker_on != self.CS.prev_right_blinker_on:
      be = car.CarState.ButtonEvent.new_message()
      be.type = 'rightBlinker'
      be.pressed = self.CS.right_blinker_on != 0
      buttonEvents.append(be)

    ret.buttonEvents = buttonEvents

    # events
    events = []
    if not self.CS.can_valid:
      self.can_invalid_count += 1
      if self.can_invalid_count >= 5:
        events.append(create_event('commIssue', [ET.NO_ENTRY, ET.IMMEDIATE_DISABLE]))
    else:
      self.can_invalid_count = 0
    if not ret.gearShifter == 'drive' and self.CP.enableDsu:
      events.append(create_event('wrongGear', [ET.NO_ENTRY, ET.SOFT_DISABLE]))
    if not self.CS.door_all_closed:
      events.append(create_event('doorOpen', [ET.NO_ENTRY, ET.SOFT_DISABLE]))
    if not self.CS.seatbelt:
      events.append(create_event('seatbeltNotLatched', [ET.NO_ENTRY, ET.SOFT_DISABLE]))
    if self.CS.esp_disabled and self.CP.enableDsu:
      events.append(create_event('espDisabled', [ET.NO_ENTRY, ET.SOFT_DISABLE]))
    if not self.CS.main_on and self.CP.enableDsu:
      events.append(create_event('wrongCarMode', [ET.NO_ENTRY, ET.USER_DISABLE]))
    if ret.gearShifter == 'reverse' and self.CP.enableDsu:
      events.append(create_event('reverseGear', [ET.NO_ENTRY, ET.IMMEDIATE_DISABLE]))
    if self.CS.steer_error:
      events.append(create_event('steerTempUnavailable', [ET.NO_ENTRY, ET.WARNING]))
    if self.CS.low_speed_lockout:
      events.append(create_event('lowSpeedLockout', [ET.NO_ENTRY]))
    if ret.vEgo < self.CP.minEnableSpeed and self.CP.enableDsu:
      events.append(create_event('speedTooLow', [ET.NO_ENTRY]))
      if c.actuators.gas > 0.1:
        # some margin on the actuator to not false trigger cancellation while stopping
        events.append(create_event('speedTooLow', [ET.IMMEDIATE_DISABLE]))
      if ret.vEgo < 0.001:
        # while in standstill, send a user alert
        events.append(create_event('manualRestart', [ET.WARNING]))

    # enable request in prius is simple, as we activate when Toyota is active (rising edge)
    if ret.cruiseState.enabled and not self.cruise_enabled_prev:
      events.append(create_event('pcmEnable', [ET.ENABLE]))
    elif not ret.cruiseState.enabled:
      events.append(create_event('pcmDisable', [ET.USER_DISABLE]))

    # disable on pedals rising edge or when brake is pressed and speed isn't zero
    if (ret.gasPressed and not self.gas_pressed_prev) or \
       (ret.brakePressed and (not self.brake_pressed_prev or ret.vEgo > 0.001)):
      events.append(create_event('pedalPressed', [ET.NO_ENTRY, ET.USER_DISABLE]))

    if ret.gasPressed:
      events.append(create_event('pedalPressed', [ET.PRE_ENABLE]))

    ret.events = events
    ret.canMonoTimes = canMonoTimes

    self.gas_pressed_prev = ret.gasPressed
    self.brake_pressed_prev = ret.brakePressed
    self.cruise_enabled_prev = ret.cruiseState.enabled

    return ret.as_reader()

  # pass in a car.CarControl
  # to be called @ 100hz
  def apply(self, c):

    self.CC.update(self.sendcan, c.enabled, self.CS, self.frame,
                   c.actuators, c.cruiseControl.cancel, c.hudControl.visualAlert,
                   c.hudControl.audibleAlert)

    self.frame += 1
    return False
