#!/usr/bin/env python3
import helics as h
import time
import numpy as np

# The faults to inject
FAULTS = ["Transformer_A", "Line_720", "Relay_1"]

def main():
    # Create federate info
    fedinfo = h.helicsCreateFederateInfo()
    h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")
    h.helicsFederateInfoSetCoreInitString(fedinfo, "--federates=1")
    
    fed = h.helicsCreateValueFederate("Fault_Publisher_Fed", fedinfo)
    
    # Register a publication
    pub = h.helicsFederateRegisterGlobalTypePublication(fed, "Relay_Sim/fault_dispatch",
     "string", '')
    
    # Enter execution mode
    h.helicsFederateEnterExecutingMode(fed)
    print("Fault publisher federate started.")
    
    current_time = 0.0
    fault_index = 0

    # Publish a random fault
    rng = np.random.randint(2)
    fault_name = FAULTS[rng]
    h.helicsPublicationPublishString(pub, fault_name)
    print(f"Published fault: {fault_name} at t={current_time}")
    

    h.helicsFederateDisconnect(fed)
    print("Fault publisher finalized.")

if __name__ == "__main__":
    main()