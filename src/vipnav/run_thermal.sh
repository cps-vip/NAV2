#!/bin/bash

mkdir -p results/
TIMESTAMP=$(date +%s)

BROKER_LOG="./results/broker_$TIMESTAMP.log"
TRANSMISSION_LOG="./results/TransmissionSim_$TIMESTAMP.log"
CC_LOG="./results/CCSim_$TIMESTAMP.log"
DISTRIBUTION_LOG="./results/DistributionSim_$TIMESTAMP.log"
RELAY_LOG="./results/RelaySim_$TIMESTAMP.log"
THERMAL_LOG="./results/ThermalSim_$TIMESTAMP.log" 

touch $BROKER_LOG $TRANSMISSION_LOG $DISTRIBUTION_LOG $CC_LOG $RELAY_LOG $THERMAL_LOG

# Ensure the Python environment is synced for HELICS
uv sync

HELICS_BROKER=`which helics_broker`
# Start broker expecting 6 federates (4 grid + 1 thermal + 1 robot)
($HELICS_BROKER -t="zmq" --federates=6 --name=mainbroker > $BROKER_LOG)&

echo "Starting Power Grid Simulators..."
cd Transmission
uv run Transmission_simulator.py > ../$TRANSMISSION_LOG 2>&1 &
cd ..

cd CC
uv run CC_simulator.py > ../$CC_LOG 2>&1 &
cd ..

cd Distribution
gridlabd IEEE_123_feeder_0.glm > ../$DISTRIBUTION_LOG 2>&1 &
cd ..

cd Relay 
uv run Relay_simulator.py > ../$RELAY_LOG 2>&1 &
cd ..

echo "Starting Thermal Fault Monitor..."
cd ThermalMonitor
uv run thermal_fault_monitor.py > ../$THERMAL_LOG 2>&1 &
cd ..

echo "Grid simulation started. The broker is now paused and waiting for your Waypoint Publisher to join."
