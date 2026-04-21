#!/usr/bin/env python3
import helics as h
import time

def main():
    fedinfo = h.helicsCreateFederateInfo()
    h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")
    h.helicsFederateInfoSetCoreInitString(fedinfo, "--federates=1")
    
    fed = h.helicsCreateValueFederate("Manual_Trigger_Fed", fedinfo)
    
    # Register a GLOBAL publication so the robot bridge finds it instantly
    pub = h.helicsFederateRegisterGlobalTypePublication(fed, "cc/thermal_fault", "string", "")
    
    h.helicsFederateEnterExecutingMode(fed)
    print("Manual Trigger Connected. Sending in 3 seconds")
    
    # Wait for the robot bridge to fully sync
    time.sleep(3)

    # Force dispatch to Line_720
    fault_payload = "Line_720"
    h.helicsPublicationPublishString(pub, fault_payload)
    
    print(f"fired: Published fault: {fault_payload}")
    
    # Give the message a second to travel before disconnecting
    time.sleep(1)
    h.helicsFederateDisconnect(fed)
    print("Manual trigger complete.")

if __name__ == "__main__":
    main()