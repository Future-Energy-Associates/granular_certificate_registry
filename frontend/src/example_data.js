const certificates = [
    {
      bundle_start_id: 1001,
      bundle_end_id: 1100,
      quantity: 100,
      issuance_id: 'ISS-001',
      device_id: 'DEV-001',
      generation_time: '2023-05-28T10:00:00Z',
    },
    {
      bundle_start_id: 1101,
      bundle_end_id: 1200,
      quantity: 100,
      issuance_id: 'ISS-002',
      device_id: 'DEV-001',
      generation_time: '2023-05-28T11:30:00Z',
    },
    {
      bundle_start_id: 1201,
      bundle_end_id: 1300,
      quantity: 100,
      issuance_id: 'ISS-003',
      device_id: 'DEV-002',
      generation_time: '2023-05-28T13:15:00Z',
    },
  ];
  
  const example_registries = [
    {
        id: 1,
        name: 'UK Registry',
        accounts: [
          { id: 1, 
            name: 'FEA Account', 
            certificates: certificates,
            devices: [{ id: 'DEV-001', name: 'Wind Turbine #1', capacity: 100 },
                      { id: 'DEV-002', name: 'Wind Turbine #2', capacity: 200} ] 
          },
          { id: 2,
            name: 'Google Account', 
            certificates: [], 
            devices: [{ id: 'DEV-003', name: 'Solar Farm #1', capacity: 150 } ] 
          },
        ],
      },
      {
        id: 2,
        name: 'Norway Registry',
        accounts: [
          { id: 3, 
            name: 'FEA Overseas Account',
            certificates: [], 
            devices: [ { id: 'DEV-001', name: 'Hydro Dam #1', capacity: 250 } ] 
          },
          { id: 4, 
            name: 'Statcraft Account', 
            certificates: [], 
            devices: [ { id: 'DEV-002', name: 'Hydro Dam #2', capacity: 500} ] 
          }
        ],
      },
      {
        id: 3,
        name: 'Unit-Based Registry',
        accounts: [
          { id: 1, 
            name: 'FEA Account', 
            certificates: [],
            devices: [{ id: 'DEV-001', name: 'Wind Turbine #1', capacity: 100 },
                      { id: 'DEV-002', name: 'Wind Turbine #2', capacity: 200} ] 
          },
          { id: 2,
            name: 'Google Account', 
            certificates: [], 
            devices: [{ id: 'DEV-003', name: 'Solar Farm #1', capacity: 150 } ] 
          },
        ],
      },
      {
        id: 4,
        name: 'Volume-Based Registry',
        accounts: [
          { id: 3, 
            name: 'FEA Overseas Account',
            certificates: [], 
            devices: [ { id: 'DEV-001', name: 'Hydro Dam #1', capacity: 250 } ] 
          },
          { id: 4, 
            name: 'Statcraft Account', 
            certificates: [], 
            devices: [ { id: 'DEV-002', name: 'Hydro Dam #2', capacity: 500} ] 
          },
        ],
      },
    ];

export default example_registries;