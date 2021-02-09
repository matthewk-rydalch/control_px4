#!/usr/bin/env python3


import asyncio

from mavsdk import System
from mavsdk.offboard import (OffboardError, VelocityNedYaw)
import navpy

from pid_class import PID


class VelCntrl:
    def __init__(self):
        self.prev_time = 0.0 #seconds
        self.ned_desired = [0.0,0.0,-2.0]

        kpN = 1.0
        kiN = 0.0
        kdN = 0.0
        tauN = 0.0
        maxNDot = 1000
        self.northPid = PID(kpN,kiN,kdN,tauN,maxNDot)

        kpE = 1.0
        kiE = 0.0
        kdE = 0.0
        tauE = 0.0
        maxEDot = 1000
        self.eastPid = PID(kpE,kiE,kdE,tauE,maxEDot)

        kpD = 1.0
        kiD = 0.0
        kdD = 0.0
        tauD = 0.0
        maxDDot = 1000
        self.downPid = PID(kpD,kiD,kdD,tauD,maxDDot)

        self.ref_set = False
        self.time_set = False

    async def run(self):
        """ Does Offboard control using velocity NED coordinates. """

        self.drone = System()
        await self.drone.connect(system_address="udp://:14540")

        print("Waiting for drone to connect...")
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print(f"Drone discovered with UUID: {state.uuid}")
                break

        print("-- Arming")
        await self.drone.action.arm()

        print("-- Setting initial setpoint")
        await self.drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))

        print("-- Starting offboard")
        try:
            await self.drone.offboard.start()
        except OffboardError as error:
            print(f"Starting offboard mode failed with error code: \
                {error._result.result}")
            print("-- Disarming")
            await self.drone.action.disarm()
            return

        # secondary_task = asyncio.ensure_future(self.get_time())

        async for lla in self.drone.telemetry.position():
            async for odom in self.drone.telemetry.odometry():
                if self.time_set:
                    self.time = odom.time_usec*1000000
                    break
                else:
                    self.prev_time = odom.time_usec*1000000
                    self.time_set = True
            if self.ref_set and self.time_set:
                cmdVel = self.get_commands(lla,self.time)
                print('cmdVel = ', cmdVel)
                await self.drone.offboard.set_velocity_ned(VelocityNedYaw(cmdVel[0],cmdVel[1],cmdVel[2], 0.0))
            else:
                self.lat_ref = lla.latitude_deg
                self.lon_ref = lla.longitude_deg
                self.alt_ref = lla.absolute_altitude_m
                self.ref_set = True

        # await secondary_task

    # async def get_time(self):
    #     async for odom in self.drone.telemetry.odometry():
    #         if self.time_set:
    #             self.time = odom.time_usec*1000000
    #         else:
    #             self.prev_time = odom.time_usec*1000000
    #             self.time_set = True
    
    # async def vel_cmds(self):
    #     async for lla in self.drone.telemetry.position():
    #         print('outside of command routine')
    #         if self.ref_set and self.time_set:
    #             print('in command routine')
    #             cmdVel = self.get_commands(lla,self.time)
    #             await self.drone.offboard.set_velocity_ned(VelocityNedYaw(cmdVel[0],cmdVel[1],cmdVel[2], 0.0))
    #         else:
    #             self.lat_ref = lla.latitude_deg
    #             self.lon_ref = lla.longitude_deg
    #             self.alt_ref = lla.absolute_altitude_m
    #             self.ref_set = True

        # await asyncio.sleep(50)

        # print("-- Go up 2 m/s")
        # await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, -2.0, 0.0))
        # await asyncio.sleep(4)

        # print("-- Go North 2 m/s, turn to face East")
        # await drone.offboard.set_velocity_ned(VelocityNedYaw(2.0, 0.0, 0.0, 90.0))
        # await asyncio.sleep(4)

        # print("-- Go South 2 m/s, turn to face West")
        # await drone.offboard.set_velocity_ned(
        #     VelocityNedYaw(-2.0, 0.0, 0.0, 270.0))
        # await asyncio.sleep(4)

        # print("-- Go West 2 m/s, turn to face East")
        # await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, -2.0, 0.0, 90.0))
        # await asyncio.sleep(4)

        # print("-- Go East 2 m/s")
        # await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 2.0, 0.0, 90.0))
        # await asyncio.sleep(4)

        # print("-- Turn to face South")
        # await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 180.0))
        # await asyncio.sleep(2)

        # print("-- Go down 1 m/s, turn to face North")
        # await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 1.0, 0.0))
        # await asyncio.sleep(4)

        # print("-- Stopping offboard")
        # try:
        #     await drone.offboard.stop()
        # except OffboardError as error:
        #     print(f"Stopping offboard mode failed with error code: \
        #         {error._result.result}")

    def get_commands(self,lla,time):
        ned = navpy.lla2ned(lla.latitude_deg,lla.longitude_deg,lla.absolute_altitude_m,self.lat_ref,self.lon_ref,self.alt_ref)
        dt = time - self.prev_time

        cmdX = self.ned_desired[0] - ned[0]
        cmdY = self.ned_desired[1] - ned[1]
        cmdZ = self.ned_desired[2] - ned[2]
        # self.northPid.update_control(ned[0],self.ned_desired[0],dt)
        # cmdX = self.northPid.command
        # self.eastPid.update_control(ned[1],self.ned_desired[1],dt)
        # cmdY = self.eastPid.command
        # self.downPid.update_control(ned[2],self.ned_desired[2],dt)
        # cmdZ = self.downPid.command

        self.prev_time = time

        cmd = [cmdX,cmdY,cmdZ]
        return cmd


if __name__ == "__main__":
    vel_cntrl = VelCntrl()
    asyncio.ensure_future(vel_cntrl.run())
    loop = asyncio.get_event_loop()
    loop.run_forever()
