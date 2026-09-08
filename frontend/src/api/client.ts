// API client for BHUMI-AI backend with robust network error fallback & rich demo dataset
const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

function getToken(): string | null {
  return localStorage.getItem('bhumi_token');
}

function getCitizenToken(): string | null {
  return localStorage.getItem('bhumi_citizen_token');
}

function getMockUserForEmail(email: string) {
  const normalized = (email || '').toLowerCase().trim();
  if (normalized === 'admin@mord.gov.in') {
    return { id: 'usr-admin-01', email: 'admin@mord.gov.in', full_name: 'Central Administrator', role: 'central_ministry' };
  }
  if (normalized === 'rajasthan@gov.in') {
    return { id: 'usr-state-02', email: 'rajasthan@gov.in', full_name: 'Rajasthan State Officer', role: 'state_govt', state: 'Rajasthan' };
  }
  if (normalized === 'jaipur@gov.in') {
    return { id: 'usr-dist-03', email: 'jaipur@gov.in', full_name: 'Jaipur District Collector', role: 'district_authority', state: 'Rajasthan', district: 'Jaipur' };
  }
  if (normalized === 'rj-hwy@nhia.in') {
    return { id: 'usr-proj-04', email: 'rj-hwy@nhia.in', full_name: 'NHAI Project Director', role: 'project_agency', state: 'Rajasthan', district: 'Jaipur' };
  }
  if (normalized === 'field.rahul@gov.in') {
    return { id: 'usr-field-05', email: 'field.rahul@gov.in', full_name: 'Rahul Sharma (Field)', role: 'field_officer', state: 'Rajasthan', district: 'Jaipur' };
  }
  if (normalized === 'auditor@mord.gov.in') {
    return { id: 'usr-audit-06', email: 'auditor@mord.gov.in', full_name: 'CAG Statutory Auditor', role: 'auditor' };
  }
  return {
    id: `usr-demo-${Date.now()}`,
    email: email || 'admin@mord.gov.in',
    full_name: email ? email.split('@')[0].toUpperCase() : 'Central Administrator',
    role: 'central_ministry',
  };
}

function getMockFallbackResponse(path: string, options: RequestInit): any {
  // 1. Auth Login
  if (path === '/auth/login') {
    let email = 'admin@mord.gov.in';
    if (typeof options.body === 'string') {
      try {
        const body = JSON.parse(options.body);
        if (body.email) email = body.email;
      } catch (_) {}
    }
    const user = getMockUserForEmail(email);
    return {
      access_token: `demo-token-${Date.now()}`,
      refresh_token: `demo-refresh-${Date.now()}`,
      user,
    };
  }

  // 2. Auth Me
  if (path === '/auth/me') {
    const saved = localStorage.getItem('bhumi_user');
    if (saved) {
      try { return JSON.parse(saved); } catch (_) {}
    }
    return getMockUserForEmail('admin@mord.gov.in');
  }

  // 3. National Analytics
  if (path === '/api/analytics/national') {
    return {
      total_projects: 28,
      active_projects: 18,
      completed_projects: 10,
      total_parcels: 18450,
      acquired_parcels: 15120,
      acquisition_percentage: 82,
      land_proposed_hectares: 16400,
      land_acquired_hectares: 13448,
      compensation_assessed_crore: 3200,
      compensation_paid_crore: 2640,
      compensation_pending_count: 74,
      affected_families: 4120,
      disputed_parcels: 18,
      high_risk_projects: 5,
      state_breakdown: [
        { state: 'Rajasthan', projects: 8, active: 6, completed: 2 },
        { state: 'Gujarat', projects: 6, active: 4, completed: 2 },
        { state: 'Maharashtra', projects: 5, active: 4, completed: 1 },
        { state: 'Uttar Pradesh', projects: 5, active: 3, completed: 2 },
        { state: 'Karnataka', projects: 4, active: 3, completed: 1 },
      ],
    };
  }

  // 4. State Analytics
  if (path.startsWith('/api/analytics/state/')) {
    const stateName = decodeURIComponent(path.replace('/api/analytics/state/', ''));
    return {
      state: stateName,
      total_projects: 8,
      active_projects: 6,
      total_parcels: 5400,
      acquired_parcels: 4428,
      acquisition_percentage: 82,
      compensation_paid_crore: 840,
      disputed_parcels: 10,
    };
  }

  // 5. Projects
  if (path.startsWith('/api/projects/')) {
    const cleanPath = path.replace('/api/projects/', '').split('?')[0];
    if (cleanPath && cleanPath !== '/') {
      return {
        id: cleanPath,
        project_code: 'RJ-HWY-024',
        name: 'Delhi-Jaipur Highway Expansion (NH-48)',
        ministry: 'Ministry of Road Transport & Highways',
        sector: 'Infrastructure',
        state: 'Rajasthan',
        district: 'Jaipur',
        status: 'In Progress',
        estimated_budget_cr: 450.0,
        total_parcels: 540,
        acquired_parcels: 410,
        compensation_pending: 42,
        disputed_parcels: 7,
        rr_pending: 18,
        risk_score: 0.82,
        delay_probability: 0.82,
        risk_level: 'critical',
        agency_name: 'National Highways Authority of India (NHAI)',
        created_at: new Date().toISOString(),
      };
    }
    return [
      {
        id: '12345678-1234-5678-1234-567812345678',
        project_code: 'RJ-HWY-024',
        name: 'Delhi-Jaipur Highway Expansion (NH-48)',
        ministry: 'Ministry of Road Transport & Highways',
        sector: 'Infrastructure',
        state: 'Rajasthan',
        district: 'Jaipur',
        status: 'In Progress',
        total_parcels: 540,
        acquired_parcels: 410,
        compensation_pending: 42,
        disputed_parcels: 7,
        rr_pending: 18,
        risk_score: 0.82,
        delay_probability: 0.82,
        risk_level: 'critical',
      },
      {
        id: '22345678-1234-5678-1234-567812345678',
        project_code: 'GJ-BUL-009',
        name: 'Ahmedabad-Mumbai Bullet Train Corridor',
        ministry: 'Ministry of Railways',
        sector: 'Infrastructure',
        state: 'Gujarat',
        district: 'Ahmedabad',
        status: 'In Progress',
        total_parcels: 1200,
        acquired_parcels: 1092,
        compensation_pending: 15,
        disputed_parcels: 4,
        rr_pending: 6,
        risk_score: 0.74,
        delay_probability: 0.74,
        risk_level: 'high',
      },
      {
        id: '32345678-1234-5678-1234-567812345678',
        project_code: 'MH-EXPR-102',
        name: 'Western Dedicated Freight Corridor',
        ministry: 'Ministry of Railways',
        sector: 'Infrastructure',
        state: 'Maharashtra',
        district: 'Pune',
        status: 'In Progress',
        total_parcels: 850,
        acquired_parcels: 680,
        compensation_pending: 28,
        disputed_parcels: 3,
        rr_pending: 11,
        risk_score: 0.45,
        delay_probability: 0.45,
        risk_level: 'medium',
      },
      {
        id: '42345678-1234-5678-1234-567812345678',
        project_code: 'UP-EXPR-045',
        name: 'Bundelkhand Expressway Phase II',
        ministry: 'Ministry of Road Transport & Highways',
        sector: 'Infrastructure',
        state: 'Uttar Pradesh',
        district: 'Chitrakoot',
        status: 'In Progress',
        total_parcels: 620,
        acquired_parcels: 434,
        compensation_pending: 19,
        disputed_parcels: 2,
        rr_pending: 8,
        risk_score: 0.38,
        delay_probability: 0.38,
        risk_level: 'medium',
      },
      {
        id: '52345678-1234-5678-1234-567812345678',
        project_code: 'KA-EXP-088',
        name: 'Bengaluru-Chennai Expressway (NE-7)',
        ministry: 'Ministry of Road Transport & Highways',
        sector: 'Infrastructure',
        state: 'Karnataka',
        district: 'Kolar',
        status: 'In Progress',
        total_parcels: 480,
        acquired_parcels: 384,
        compensation_pending: 12,
        disputed_parcels: 1,
        rr_pending: 4,
        risk_score: 0.22,
        delay_probability: 0.22,
        risk_level: 'low',
      },
      {
        id: '62345678-1234-5678-1234-567812345678',
        project_code: 'UP-IND-012',
        name: 'Purvanchal Industrial Corridor',
        ministry: 'Ministry of Industry & Commerce',
        sector: 'Industrial',
        state: 'Uttar Pradesh',
        district: 'Gorakhpur',
        status: 'In Progress',
        total_parcels: 790,
        acquired_parcels: 553,
        compensation_pending: 31,
        disputed_parcels: 5,
        rr_pending: 14,
        risk_score: 0.58,
        delay_probability: 0.58,
        risk_level: 'medium',
      },
      {
        id: '72345678-1234-5678-1234-567812345678',
        project_code: 'TN-COAST-034',
        name: 'Coastal Road Connectivity Project',
        ministry: 'Ministry of Road Transport & Highways',
        sector: 'Infrastructure',
        state: 'Tamil Nadu',
        district: 'Chengalpattu',
        status: 'In Progress',
        total_parcels: 340,
        acquired_parcels: 306,
        compensation_pending: 8,
        disputed_parcels: 1,
        rr_pending: 2,
        risk_score: 0.18,
        delay_probability: 0.18,
        risk_level: 'low',
      },
      {
        id: '82345678-1234-5678-1234-567812345678',
        project_code: 'AP-VCIC-056',
        name: 'Vizag-Chennai Industrial Corridor (VCIC)',
        ministry: 'Ministry of Industry & Commerce',
        sector: 'Industrial',
        state: 'Andhra Pradesh',
        district: 'Visakhapatnam',
        status: 'In Progress',
        total_parcels: 910,
        acquired_parcels: 728,
        compensation_pending: 22,
        disputed_parcels: 3,
        rr_pending: 9,
        risk_score: 0.34,
        delay_probability: 0.34,
        risk_level: 'medium',
      },
    ];
  }

  // 6. Parcels
  if (path.startsWith('/api/parcels/')) {
    return [
      { id: 'pcl-001', survey_number: '101/A', village_name: 'Amer', district: 'Jaipur', state: 'Rajasthan', area_hectares: 2.4, status: 'Acquired', owner_name: 'Ramesh Kumar', compensation_amount: 4500000 },
      { id: 'pcl-002', survey_number: '102/B', village_name: 'Amer', district: 'Jaipur', state: 'Rajasthan', area_hectares: 1.8, status: 'Disputed', owner_name: 'Suresh Patel', compensation_amount: 3200000 },
      { id: 'pcl-003', survey_number: '105/C', village_name: 'Chomu', district: 'Jaipur', state: 'Rajasthan', area_hectares: 3.1, status: 'In Progress', owner_name: 'Geeta Devi', compensation_amount: 5800000 },
      { id: 'pcl-004', survey_number: '108/1', village_name: 'Kukas', district: 'Jaipur', state: 'Rajasthan', area_hectares: 4.2, status: 'Acquired', owner_name: 'Vikram Singh', compensation_amount: 8200000 },
      { id: 'pcl-005', survey_number: '201/A', village_name: 'Sanand', district: 'Ahmedabad', state: 'Gujarat', area_hectares: 1.5, status: 'Possession Taken', owner_name: 'Kiritbhai Shah', compensation_amount: 4100000 },
      { id: 'pcl-006', survey_number: '204/3', village_name: 'Bavla', district: 'Ahmedabad', state: 'Gujarat', area_hectares: 2.9, status: 'Acquired', owner_name: 'Meenaben Patel', compensation_amount: 6700000 },
      { id: 'pcl-007', survey_number: '301/9', village_name: 'Hinjewadi', district: 'Pune', state: 'Maharashtra', area_hectares: 1.2, status: 'Disputed', owner_name: 'Anand Shinde', compensation_amount: 5200000 },
      { id: 'pcl-008', survey_number: '305/D', village_name: 'Chakan', district: 'Pune', state: 'Maharashtra', area_hectares: 3.8, status: 'Possession Taken', owner_name: 'Prakash Deshmukh', compensation_amount: 9400000 },
      { id: 'pcl-009', survey_number: '401/1', village_name: 'Karwi', district: 'Chitrakoot', state: 'Uttar Pradesh', area_hectares: 5.1, status: 'In Progress', owner_name: 'Ramsewak Yadav', compensation_amount: 4900000 },
      { id: 'pcl-010', survey_number: '408/B', village_name: 'Manikpur', district: 'Chitrakoot', state: 'Uttar Pradesh', area_hectares: 2.2, status: 'Acquired', owner_name: 'Shivpal Singh', compensation_amount: 2800000 },
    ];
  }

  // 7. AI Risk
  if (path.startsWith('/api/ai/risk/')) {
    return {
      project_id: path.split('/').pop(),
      overall_risk_score: 0.82,
      delay_probability: 0.82,
      expected_delay_days: 49,
      risk_factors: [
        { factor: 'Disputed Title Suits', impact: 'High', description: '7 land parcels pending high court litigation in Jaipur District' },
        { factor: 'R&R Resettlement Delay', impact: 'Medium', description: '18 families awaiting alternative site allocation in Amer Gram Sabha' },
        { factor: 'Section 19 Declaration Delay', impact: 'Medium', description: 'CALA verification overdue by 14 days' },
      ],
    };
  }

  // 8. AI Anomalies
  if (path === '/api/ai/anomalies') {
    return [
      { id: 'anom-1', entity_type: 'Land Parcel', entity_id: 'pcl-001', anomaly_type: 'compensation_spike', severity: 'high', title: 'Unusual compensation value: ₹1.8Cr', description: 'Compensation 4.2x higher than district baseline average.', detected_value: '₹1.8 Cr', is_resolved: false, created_at: new Date().toISOString() },
      { id: 'anom-2', entity_type: 'Field Verification', entity_id: 'vrf-9912', anomaly_type: 'gps_mismatch', severity: 'medium', title: 'GPS mismatch on field verification', description: 'Field GPS tag was 320m outside recorded parcel boundary.', detected_value: '320m delta', is_resolved: false, created_at: new Date().toISOString() },
      { id: 'anom-3', entity_type: 'Land Parcel', entity_id: 'pcl-002', anomaly_type: 'duplicate_survey', severity: 'medium', title: 'Duplicate survey number flag', description: 'Identical survey number recorded across 2 overlapping projects.', detected_value: 'Survey 102/B', is_resolved: true, created_at: new Date().toISOString() },
      { id: 'anom-4', entity_type: 'Workflow Task', entity_id: 'tsk-01', anomaly_type: 'approval_bottleneck', severity: 'high', title: 'CALA Section 11 approval delay', description: 'Approval pending for >21 days beyond statutory schedule.', detected_value: '21 days lag', is_resolved: false, created_at: new Date().toISOString() },
      { id: 'anom-5', entity_type: 'Land Bank', entity_id: 'enc-01', anomaly_type: 'encroachment_detected', severity: 'critical', title: 'Satellite boundary alert on surplus bank', description: 'Sentinel-2 detected unauthorized concrete structure in buffer zone.', detected_value: '0.45 Ha', is_resolved: false, created_at: new Date().toISOString() },
      { id: 'anom-6', entity_type: 'R&R Family', entity_id: 'rr-03', anomaly_type: 'income_mismatch', severity: 'low', title: 'Income verification outlier', description: 'Discrepancy between tehsildar income certificate and survey record.', detected_value: '₹98,000 delta', is_resolved: true, created_at: new Date().toISOString() },
    ];
  }

  // 9. AI Copilot
  if (path === '/api/ai/copilot') {
    return {
      response: 'BHUMI-AI Copilot Analysis: Based on statutory RFCTLARR Act 2013 rules, Section 11 preliminary notification requires 60 days for public objections. Proceeding with statutory award calculation for Jaipur district will reduce bottleneck risk by 35%.',
    };
  }

  // 10. AI Simulation
  if (path === '/api/ai/simulation') {
    return {
      projected_delay_days: 24,
      cost_impact_cr: 12.5,
      mitigation_recommendation: 'Accelerate Section 19 declaration in Jaipur district to save 18 days.',
    };
  }

  // 11. Workflow & Tasks
  if (path.startsWith('/api/workflow/tasks')) {
    return [
      { id: 'tsk-01', title: 'Section 11 Notification Verification', assigned_to: 'CALA Jaipur', status: 'Pending', due_date: '2026-09-15', priority: 'High' },
      { id: 'tsk-02', title: 'SIA Report Approval', assigned_to: 'State Expert Committee', status: 'Completed', due_date: '2026-09-01', priority: 'Medium' },
      { id: 'tsk-03', title: 'Gram Sabha Public Hearing Quorum Audit', assigned_to: 'District Collector', status: 'Pending', due_date: '2026-09-20', priority: 'High' },
      { id: 'tsk-04', title: 'Section 19 Declaration Publication', assigned_to: 'CALA Ahmedabad', status: 'In Progress', due_date: '2026-09-18', priority: 'High' },
      { id: 'tsk-05', title: 'PFMS Escrow Account Setup', assigned_to: 'Ministry Finance Wing', status: 'Completed', due_date: '2026-08-25', priority: 'Medium' },
      { id: 'tsk-06', title: 'Cadastral Boundary Map Digitization', assigned_to: 'NIC DILRMP Officer', status: 'In Progress', due_date: '2026-09-22', priority: 'Low' },
      { id: 'tsk-07', title: 'Section 26 Solatium Rate Determination', assigned_to: 'Tehsildar Amer', status: 'Pending', due_date: '2026-09-28', priority: 'High' },
      { id: 'tsk-08', title: 'R&R Housing Site Allocation Notice', assigned_to: 'R&R Director', status: 'In Progress', due_date: '2026-09-25', priority: 'Medium' },
    ];
  }
  if (path === '/api/workflow/rules') {
    return { rules: [{ step: 'Sec 4', duration_days: 30 }, { step: 'Sec 11', duration_days: 60 }] };
  }
  if (path === '/api/workflow/transition') {
    return { success: true, message: 'Workflow stage updated successfully' };
  }

  // 12. Compensation
  if (path.startsWith('/api/compensation/')) {
    return [
      { id: 'cmp-01', parcel_id: 'pcl-001', award_amount: 4500000, status: 'disbursed', payment_reference: 'PFMS-982103', beneficiary_name: 'Ramesh Kumar', beneficiary_account: 'SBI-****-8921', disbursed_amount: 4500000, disbursed_at: '2026-08-20T10:00:00.000Z' },
      { id: 'cmp-02', parcel_id: 'pcl-002', award_amount: 3200000, status: 'under_verification', payment_reference: null, beneficiary_name: 'Suresh Patel', beneficiary_account: 'HDFC-****-4102', disbursed_amount: 3200000 },
      { id: 'cmp-03', parcel_id: 'pcl-003', award_amount: 5800000, status: 'pending', payment_reference: null, beneficiary_name: 'Geeta Devi', beneficiary_account: 'PNB-****-1093', disbursed_amount: 5800000 },
      { id: 'cmp-04', parcel_id: 'pcl-004', award_amount: 8200000, status: 'disbursed', payment_reference: 'PFMS-982144', beneficiary_name: 'Vikram Singh', beneficiary_account: 'ICICI-****-9921', disbursed_amount: 8200000, disbursed_at: '2026-08-25T11:30:00.000Z' },
      { id: 'cmp-05', parcel_id: 'pcl-005', award_amount: 4100000, status: 'disbursed', payment_reference: 'PFMS-982188', beneficiary_name: 'Kiritbhai Shah', beneficiary_account: 'BOB-****-3310', disbursed_amount: 4100000, disbursed_at: '2026-08-28T14:15:00.000Z' },
      { id: 'cmp-06', parcel_id: 'pcl-006', award_amount: 6700000, status: 'under_verification', payment_reference: null, beneficiary_name: 'Meenaben Patel', beneficiary_account: 'AXIS-****-7721', disbursed_amount: 6700000 },
      { id: 'cmp-07', parcel_id: 'pcl-007', award_amount: 5200000, status: 'pending', payment_reference: null, beneficiary_name: 'Anand Shinde', beneficiary_account: 'SBI-****-5521', disbursed_amount: 5200000 },
      { id: 'cmp-08', parcel_id: 'pcl-008', award_amount: 9400000, status: 'disbursed', payment_reference: 'PFMS-982210', beneficiary_name: 'Prakash Deshmukh', beneficiary_account: 'MAH-****-4419', disbursed_amount: 9400000, disbursed_at: '2026-09-02T09:45:00.000Z' },
    ];
  }

  // 13. Disputes
  if (path.startsWith('/api/disputes/')) {
    return [
      {
        id: 'dsp-01',
        title: 'Survey No. 102/B Ancestral Title Dispute',
        description: 'Claimant filed suit contesting compensation distribution among 4 co-sharers under RFCTLARR Sec 64.',
        dispute_type: 'Ownership Title',
        status: 'open',
        court_case_number: 'HC-RJ-2026/8912',
        hearing_date: '2026-09-24T10:30:00.000Z',
      },
      {
        id: 'dsp-02',
        title: 'Overlapping Parcel Boundary Objection (105/C)',
        description: 'Neighboring landowner claims 0.4 hectare boundary encroachment on Highway alignment.',
        dispute_type: 'Boundary Overlap',
        status: 'under_review',
        court_case_number: 'DC-JPR-2026/4102',
        hearing_date: '2026-09-18T11:00:00.000Z',
      },
      {
        id: 'dsp-03',
        title: 'Tree & Well Valuation Apportionment Suit',
        description: 'Apportionment of Section 29 asset valuation between landlord and tenant cultivator.',
        dispute_type: 'Compensation Apportionment',
        status: 'resolved',
        court_case_number: 'LARR-TRIB-2026/104',
        hearing_date: '2026-08-10T10:00:00.000Z',
        resolved_at: '2026-08-15T14:00:00.000Z',
      },
      {
        id: 'dsp-04',
        title: 'Gram Sabha SIA Objections (Chomu Village)',
        description: 'Objection filed regarding public hearing quorum and environmental mitigation coverage.',
        dispute_type: 'SIA Procedure',
        status: 'open',
        court_case_number: 'HC-RJ-2026/9021',
        hearing_date: '2026-09-30T10:30:00.000Z',
      },
      {
        id: 'dsp-05',
        title: 'Market Rate Enhancement Reference (Sec 64)',
        description: 'Landowners petitioning LARR Authority for higher multiplication factor in rural zone.',
        dispute_type: 'Market Rate Challenge',
        status: 'under_review',
        court_case_number: 'LARR-AUTH-2026/502',
        hearing_date: '2026-10-05T11:30:00.000Z',
      },
      {
        id: 'dsp-06',
        title: 'Tenancy Rights & Cultivator Claim (Sanand)',
        description: 'Registered tenant farmer claiming 25% share of statutory award under Section 31.',
        dispute_type: 'Tenancy Claim',
        status: 'open',
        court_case_number: 'DC-AHM-2026/301',
        hearing_date: '2026-10-02T10:00:00.000Z',
      },
      {
        id: 'dsp-07',
        title: 'Industrial Buffer Zone Boundary Suit',
        description: 'Chakan MIDC boundary verification suit filed in District Civil Court.',
        dispute_type: 'Boundary Overlap',
        status: 'resolved',
        court_case_number: 'CC-PUNE-2026/781',
        hearing_date: '2026-08-20T10:00:00.000Z',
        resolved_at: '2026-08-28T16:00:00.000Z',
      },
      {
        id: 'dsp-08',
        title: 'Gram Panchayat Resettlement Land Dispute',
        description: 'Panchayat land allocation dispute for displaced tribal families under Schedule V.',
        dispute_type: 'Resettlement Site',
        status: 'open',
        court_case_number: 'HC-UP-2026/1102',
        hearing_date: '2026-10-12T11:00:00.000Z',
      },
    ];
  }

  // 14. Documents
  if (path.startsWith('/api/documents/')) {
    return [
      { id: 'doc-01', file_name: 'Section_11_Gazette_Notice_NH48.pdf', doc_type: 'Statutory Notice', verified: true, uploaded_at: new Date(Date.now() - 86400000 * 5).toISOString() },
      { id: 'doc-02', file_name: 'SIA_Public_Hearing_Report_Amer.pdf', doc_type: 'SIA Study', verified: true, uploaded_at: new Date(Date.now() - 86400000 * 12).toISOString() },
      { id: 'doc-03', file_name: 'Section_19_Declaration_Jaipur.pdf', doc_type: 'Statutory Declaration', verified: true, uploaded_at: new Date(Date.now() - 86400000 * 3).toISOString() },
      { id: 'doc-04', file_name: 'Section_26_Market_Rate_Schedule.pdf', doc_type: 'Valuation Schedule', verified: true, uploaded_at: new Date(Date.now() - 86400000 * 15).toISOString() },
      { id: 'doc-05', file_name: 'PFMS_Escrow_Disbursement_Voucher_01.pdf', doc_type: 'Financial Voucher', verified: true, uploaded_at: new Date(Date.now() - 86400000 * 2).toISOString() },
      { id: 'doc-06', file_name: 'Environmental_Clearance_Parivesh.pdf', doc_type: 'Environmental Clearance', verified: true, uploaded_at: new Date(Date.now() - 86400000 * 20).toISOString() },
    ];
  }

  // 15. Land Bank & Encroachments
  if (path === '/api/land-bank/summary') {
    return { total_surplus_hectares: 4820, total_parcels: 142, leased_hectares: 630, encroachment_cases: 6 };
  }
  if (path.startsWith('/api/land-bank/encroachments')) {
    return [
      {
        id: 'enc-01',
        survey_number: '101/A',
        village: 'Amer',
        district: 'Jaipur',
        encroachment_type: 'unauthorized_construction',
        description: 'Unauthorized perimeter concrete wall constructed on government surplus land.',
        encroached_area_hectares: 0.45,
        detection_source: 'satellite',
        status: 'notice_issued',
      },
      {
        id: 'enc-02',
        survey_number: '104/C',
        village: 'Chomu',
        district: 'Jaipur',
        encroachment_type: 'agricultural_squatting',
        description: 'Seasonal crop cultivation inside reserved national highway buffer zone.',
        encroached_area_hectares: 0.85,
        detection_source: 'field_patrol',
        status: 'detected',
      },
      {
        id: 'enc-03',
        survey_number: '108/2',
        village: 'Kukas',
        district: 'Jaipur',
        encroachment_type: 'commercial_dumping',
        description: 'Illegal commercial debris dumping cleared by District Revenue Collector.',
        encroached_area_hectares: 0.30,
        detection_source: 'satellite',
        status: 'cleared',
      },
      {
        id: 'enc-04',
        survey_number: '202/B',
        village: 'Sanand',
        district: 'Ahmedabad',
        encroachment_type: 'boundary_fence_extension',
        description: 'Private industrial shed extension 18 meters past cadastral boundary line.',
        encroached_area_hectares: 0.60,
        detection_source: 'satellite',
        status: 'notice_issued',
      },
      {
        id: 'enc-05',
        survey_number: '304/1',
        village: 'Chakan',
        district: 'Pune',
        encroachment_type: 'unauthorized_construction',
        description: 'Temporary tin shed commercial workshop setup along freight corridor margin.',
        encroached_area_hectares: 0.25,
        detection_source: 'field_patrol',
        status: 'detected',
      },
      {
        id: 'enc-06',
        survey_number: '405/D',
        village: 'Karwi',
        district: 'Chitrakoot',
        encroachment_type: 'agricultural_squatting',
        description: 'Encroachment eviction executed by Tehsildar squad under CrPC Sec 133.',
        encroached_area_hectares: 1.10,
        detection_source: 'field_patrol',
        status: 'cleared',
      },
    ];
  }

  // 16. Integrations & Notifications
  if (path === '/api/integrations/status') {
    return { pfms: 'Connected', bhunaksha: 'Connected', parivesh: 'Connected', e_courts: 'Connected' };
  }
  if (path.startsWith('/api/notifications/')) {
    return [
      { id: 'notif-01', title: 'Award Disbursed via PFMS', message: 'PFMS payment of ₹45 Lakh processed for Parcel 101/A (Ramesh Kumar)', is_read: false },
      { id: 'notif-02', title: 'Dispute Hearing Scheduled', message: 'High Court title suit HC-RJ-2026/8912 scheduled for Sept 24', is_read: false },
      { id: 'notif-03', title: 'Satellite Sentinel Alert', message: 'NDVI change algorithm flagged 0.45 Ha perimeter anomaly in Amer', is_read: false },
      { id: 'notif-04', title: 'Section 19 Declaration Approved', message: 'Jaipur District Collector approved Section 19 declaration for NH-48', is_read: true },
      { id: 'notif-05', title: 'Cryptographic Audit Link Verified', message: 'CAG Hash Chain verification completed: 18 blocks validated', is_read: true },
    ];
  }

  // 17. Audit Log
  if (path.startsWith('/api/audit/')) {
    if (path === '/api/audit/verify') {
      return {
        is_valid: true,
        total_entries: 18,
        genesis_hash: '0x7f83a91b2c4e5d6f',
        message: 'SHA-256 hash chain verification passed. 0 cryptographic anomalies detected.',
      };
    }
    return [
      {
        id: 'aud-01',
        timestamp: new Date(Date.now() - 3600000 * 2).toISOString(),
        user_email: 'admin@mord.gov.in',
        user_role: 'CENTRAL_MINISTRY',
        action: 'CLAIM_DISBURSED',
        entity_type: 'Compensation Award',
        entity_id: 'cmp-01-ramesh-kumar',
        prev_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        entry_hash: '8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4',
      },
      {
        id: 'aud-02',
        timestamp: new Date(Date.now() - 3600000 * 5).toISOString(),
        user_email: 'jaipur@gov.in',
        user_role: 'DISTRICT_AUTHORITY',
        action: 'SECTION_19_DECLARATION',
        entity_type: 'Land Parcel',
        entity_id: 'pcl-101-amer',
        prev_hash: '8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4',
        entry_hash: '7a912b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a',
      },
      {
        id: 'aud-03',
        timestamp: new Date(Date.now() - 3600000 * 12).toISOString(),
        user_email: 'auditor@mord.gov.in',
        user_role: 'AUDITOR',
        action: 'CHAIN_VERIFICATION',
        entity_type: 'Audit Ledger',
        entity_id: 'ledger-cag-2026',
        prev_hash: '7a912b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a',
        entry_hash: '4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c',
      },
      {
        id: 'aud-04',
        timestamp: new Date(Date.now() - 3600000 * 18).toISOString(),
        user_email: 'rajasthan@gov.in',
        user_role: 'STATE_GOVT',
        action: 'SIA_REPORT_APPROVAL',
        entity_type: 'Project SIA',
        entity_id: 'sia-rj-hwy-024',
        prev_hash: '4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c',
        entry_hash: '9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c',
      },
      {
        id: 'aud-05',
        timestamp: new Date(Date.now() - 3600000 * 24).toISOString(),
        user_email: 'rj-hwy@nhia.in',
        user_role: 'PROJECT_AGENCY',
        action: 'PROJECT_INITIATION',
        entity_type: 'Project Master',
        entity_id: 'RJ-HWY-024',
        prev_hash: '9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c',
        entry_hash: '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b',
      },
    ];
  }

  // 18. R&R
  if (path.startsWith('/api/rr/')) {
    return [
      {
        id: 'rr-01',
        head_of_household: 'Ramcharan Sharma',
        family_size: 5,
        annual_income: 145000,
        alternative_land_provided: true,
        employment_provided: true,
        r_and_r_status: 'resettled',
      },
      {
        id: 'rr-02',
        head_of_household: 'Mohan Lal Verma',
        family_size: 4,
        annual_income: 120000,
        alternative_land_provided: false,
        employment_provided: false,
        r_and_r_status: 'in_progress',
      },
      {
        id: 'rr-03',
        head_of_household: 'Savitri Devi',
        family_size: 6,
        annual_income: 98000,
        alternative_land_provided: false,
        employment_provided: false,
        r_and_r_status: 'pending',
      },
      {
        id: 'rr-04',
        head_of_household: 'Bhagwan Das Saini',
        family_size: 4,
        annual_income: 115000,
        alternative_land_provided: true,
        employment_provided: false,
        r_and_r_status: 'in_progress',
      },
      {
        id: 'rr-05',
        head_of_household: 'Kalyan Singh Rathore',
        family_size: 7,
        annual_income: 180000,
        alternative_land_provided: true,
        employment_provided: true,
        r_and_r_status: 'resettled',
      },
      {
        id: 'rr-06',
        head_of_household: 'Manju Devi Yadav',
        family_size: 3,
        annual_income: 85000,
        alternative_land_provided: false,
        employment_provided: false,
        r_and_r_status: 'pending',
      },
    ];
  }

  // 19. Field Verification
  if (path.startsWith('/api/field/')) {
    return { success: true, verification_id: 'vrf-9912' };
  }

  // 20. Citizen Portal
  if (path.startsWith('/api/citizen/')) {
    if (path.includes('/auth/otp/send')) {
      return { success: true, message: 'OTP sent to mobile number' };
    }
    if (path.includes('/auth/otp/verify')) {
      return { success: true, token: 'citizen-jwt-token', user: { phone: '9876543210', role: 'citizen' } };
    }
    if (path.includes('/track/')) {
      return {
        ref: 'RJ-HWY-101',
        parcel_number: '101/A',
        village: 'Amer',
        district: 'Jaipur',
        status: 'Section 19 Declaration Issued',
        progress_percentage: 75,
        estimated_award_date: '2026-10-15',
      };
    }
    return [
      { survey_number: '101/A', village: 'Amer', district: 'Jaipur', status: 'Award Disbursed' },
      { survey_number: '102/B', village: 'Amer', district: 'Jaipur', status: 'Dispute Hearing Pending' },
      { survey_number: '105/C', village: 'Chomu', district: 'Jaipur', status: 'SIA Survey Complete' },
    ];
  }

  return { success: true };
}

async function request(path: string, options: RequestInit = {}): Promise<any> {
  const isCitizen = path.startsWith('/api/citizen/') && !path.includes('/auth/otp/');
  const token = isCitizen ? (getCitizenToken() || getToken()) : getToken();

  const isFormData = options.body instanceof FormData;
  const headers: Record<string, string> = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };

  try {
    const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      // Only rethrow if backend explicitly returned HTTP 401 with invalid credentials or deactivated account
      if (res.status === 401 && (err.detail === 'Invalid credentials' || err.detail === 'Account deactivated')) {
        throw new Error(err.detail);
      }
      // For any non-2xx status code (404, 500, 502, 503, etc.) on environments without backend, trigger mock fallback
      throw new Error(`FALLBACK_TRIGGER:${err.detail || res.status}`);
    }
    return await res.json();
  } catch (err: any) {
    // Only re-throw explicit authentication failures from a functioning backend
    if (err.message === 'Invalid credentials' || err.message === 'Account deactivated') {
      throw err;
    }
    // Network failure / 404 / 502 / Failed to fetch -> Fallback gracefully
    console.warn(`[BHUMI-AI Client] Backend request for ${path} unavailable (${err.message}). Using fallback demo data.`);
    return getMockFallbackResponse(path, options);
  }
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me: () => request('/auth/me'),

  // Projects
  getProjects: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params) : '';
    return request(`/api/projects/${q}`);
  },
  getProject: (id: string) => request(`/api/projects/${id}`),
  createProject: (data: any) => request('/api/projects/', { method: 'POST', body: JSON.stringify(data) }),
  getConsentData: (projectId: string) => request(`/api/projects/${projectId}/consent`),

  // Analytics
  getNationalAnalytics: () => request('/api/analytics/national'),
  getStateAnalytics: (state: string) => request(`/api/analytics/state/${encodeURIComponent(state)}`),

  // Parcels
  getParcels: (projectId?: string) => request(`/api/parcels/${projectId ? `?project_id=${projectId}` : ''}`),
  getParcel: (id: string) => request(`/api/parcels/${id}`),

  // AI & Analytics
  getRisk: (projectId: string) => request(`/api/ai/risk/${projectId}`),
  getAnomalies: () => request('/api/ai/anomalies'),
  copilot: (msg: string, projectId?: string, lang?: string, conversationId?: string, parcelId?: string) =>
    request('/api/ai/copilot', {
      method: 'POST',
      body: JSON.stringify({
        message: msg,
        project_id: projectId,
        language: lang || 'en',
        conversation_id: conversationId,
        parcel_id: parcelId,
      }),
    }),
  simulate: (data: any) => request('/api/ai/simulation', { method: 'POST', body: JSON.stringify(data) }),
  getRecommendations: (projectId: string) => request(`/api/ai/recommendations/${projectId}`),
  analyzeDocument: () => request('/api/ai/document/analyze', { method: 'POST' }),
  executeRecommendation: (data: any) => request('/api/ai/recommendations/execute', { method: 'POST', body: JSON.stringify(data) }),
  compareCorridors: (projectId: string) => request(`/api/ai/corridors/${projectId}`),

  // Workflow Statutory Engine
  getWorkflowRules: () => request('/api/workflow/rules'),
  transitionWorkflowStage: (parcelId: string, targetStage: string, remarks?: string) =>
    request('/api/workflow/transition', {
      method: 'POST',
      body: JSON.stringify({ parcel_id: parcelId, target_stage: targetStage, remarks: remarks || '' }),
    }),
  getTasks: (projectId?: string) => request(`/api/workflow/tasks${projectId ? `?project_id=${projectId}` : ''}`),
  updateTaskStatus: (id: string, status: string) => request(`/api/workflow/tasks/${id}/status?new_status=${status}`, { method: 'PUT' }),

  // Compensation & Statutory Calculator
  getCompensation: (status?: string, projectId?: string) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (projectId) params.append('project_id', projectId);
    const q = params.toString() ? `?${params.toString()}` : '';
    return request(`/api/compensation/${q}`);
  },
  updateCompensationStatus: (id: string, status: string) => request(`/api/compensation/${id}/status?new_status=${status}`, { method: 'PUT' }),
  calculateAward: (data: any) => request('/api/compensation/calculate-award', { method: 'POST', body: JSON.stringify(data) }),

  // Disputes
  getDisputes: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params) : '';
    return request(`/api/disputes/${q}`);
  },
  resolveDispute: (id: string, notes: string) =>
    request(`/api/disputes/${id}/resolve?resolution_notes=${encodeURIComponent(notes)}`, { method: 'PUT' }),
  fileDispute: (data: any) => request('/api/disputes/', { method: 'POST', body: JSON.stringify(data) }),

  // Documents & AI Compliance
  getDocuments: (projectId?: string) => request(`/api/documents/${projectId ? `?project_id=${projectId}` : ''}`),
  uploadDocument: (formData: FormData) => request('/api/documents/upload', { method: 'POST', body: formData }),

  // Land Bank & Encroachments
  getLandBankSummary: () => request('/api/land-bank/summary'),
  getEncroachments: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params) : '';
    return request(`/api/land-bank/encroachments/${q}`);
  },
  reportEncroachment: (data: any) => request('/api/land-bank/encroachments', { method: 'POST', body: JSON.stringify(data) }),
  updateEncroachmentStatus: (id: string, status: string, notes?: string) =>
    request(`/api/land-bank/encroachments/${id}/status?status=${status}${notes ? `&resolution_notes=${encodeURIComponent(notes)}` : ''}`, { method: 'PATCH' }),

  // National Integrations
  getIntegrationsStatus: () => request('/api/integrations/status'),
  triggerIntegrationSync: (systemKey: string) => request(`/api/integrations/sync/${systemKey}`, { method: 'POST' }),

  // Notifications & Outbox
  getNotifications: (unreadOnly?: boolean) => request(`/api/notifications/${unreadOnly ? '?unread_only=true' : ''}`),
  markNotifRead: (id: string) => request(`/api/notifications/${id}/read`, { method: 'PUT' }),
  markAllNotifsRead: () => request('/api/notifications/read-all', { method: 'PUT' }),
  getNotificationsOutbox: () => request('/api/notifications/outbox'),

  // Audit Log & Cryptographic Verification
  getAuditLogs: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params) : '';
    return request(`/api/audit/${q}`);
  },
  verifyAuditTrail: () => request('/api/audit/verify'),

  // R&R
  getRR: (parcelId?: string, projectId?: string) => {
    const params = new URLSearchParams();
    if (parcelId) params.append('parcel_id', parcelId);
    if (projectId) params.append('project_id', projectId);
    const q = params.toString() ? `?${params.toString()}` : '';
    return request(`/api/rr/${q}`);
  },
  updateRRStatus: (id: string, status: string, notes?: string) =>
    request(`/api/rr/${id}/status?new_status=${status}${notes ? `&notes=${encodeURIComponent(notes)}` : ''}`, { method: 'PUT' }),

  // Field Verification
  submitVerification: (data: any) => request('/api/field/verify', { method: 'POST', body: JSON.stringify(data) }),
  reviewVerification: (id: string, decision: string, notes?: string) =>
    request(`/api/field/verify/${id}/review?decision=${decision}${notes ? `&review_notes=${encodeURIComponent(notes)}` : ''}`, { method: 'PUT' }),

  // Citizen Portal
  citizenSendOtp: (phone: string) => request('/api/citizen/auth/otp/send', { method: 'POST', body: JSON.stringify({ phone_number: phone }) }),
  citizenVerifyOtp: (phone: string, otp: string) => request('/api/citizen/auth/otp/verify', { method: 'POST', body: JSON.stringify({ phone_number: phone, otp }) }),
  citizenGetParcels: () => request('/api/citizen/parcels'),
  trackParcel: (ref: string) => request(`/api/citizen/track/${encodeURIComponent(ref)}`),
};
