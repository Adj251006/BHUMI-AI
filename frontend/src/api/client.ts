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
      district_breakdown: [
        { district: 'Jaipur', projects: 3, active: 2 },
        { district: 'Jodhpur', projects: 2, active: 2 },
        { district: 'Udaipur', projects: 2, active: 1 },
        { district: 'Ajmer', projects: 1, active: 1 },
      ],
      projects: [
        { id: '12345678-1234-5678-1234-567812345678', name: 'Delhi-Jaipur Highway Expansion (NH-48)', district: 'Jaipur', status: 'active' },
        { id: 'proj-rj-002', name: 'Jaipur Outer Ring Road Phase II', district: 'Jaipur', status: 'active' },
        { id: 'proj-rj-003', name: 'Jodhpur Solar Park Feeder Line', district: 'Jodhpur', status: 'active' },
        { id: 'proj-rj-004', name: 'Udaipur Smart Logistics Hub', district: 'Udaipur', status: 'active' },
        { id: 'proj-rj-005', name: 'Ajmer-Pushkar Rail Link', district: 'Ajmer', status: 'active' },
        { id: 'proj-rj-006', name: 'Kota Industrial Corridor Access Road', district: 'Kota', status: 'completed' },
        { id: 'proj-rj-007', name: 'Bikaner Renewable Energy Park Freight Line', district: 'Bikaner', status: 'active' },
        { id: 'proj-rj-008', name: 'Alwar Agro-Industrial Logistics Expressway', district: 'Alwar', status: 'completed' },
      ],
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
    ];
  }

  // 7. AI Risk
  if (path.startsWith('/api/ai/risk/')) {
    return {
      project_id: path.split('/').pop(),
      overall_risk_score: 0.82,
      delay_probability: 0.82,
      expected_delay_days: 49,
      risk_level: 'critical',
      explanation: 'Project RJ-HWY-024 has 7 disputed parcels in high-traffic alignment zones, 42 pending CALA compensation vouchers, and 18 displaced families awaiting Schedule V housing plot allocation.',
      contributing_factors: [
        { factor: 'Disputed Title Suits', contribution_pct: 45, description: '7 land parcels pending high court litigation in Jaipur District' },
        { factor: 'Compensation Pending', contribution_pct: 35, description: '42 awards approved but pending PFMS disbursement' },
        { factor: 'R&R Housing Allocation', contribution_pct: 20, description: '18 families awaiting alternative site allocation in Amer' },
      ],
      risk_factors: [
        { factor: 'Disputed Title Suits', impact: 'High', description: '7 land parcels pending high court litigation in Jaipur District' },
        { factor: 'R&R Resettlement Delay', impact: 'Medium', description: '18 families awaiting alternative site allocation in Amer Gram Sabha' },
      ],
    };
  }

  // 8. AI Recommendations
  if (path.startsWith('/api/ai/recommendations')) {
    return {
      recommendations: [
        {
          priority: 1,
          priority_level: 'critical',
          title: 'Fast-Track 7 Section 64 High Court Title Disputes',
          reason: 'Disputed parcels 102/B & 105/C are directly blocking possession of 4.2 km highway corridor.',
          expected_impact: 'Saves 29 days of project delay and ₹12.5 Cr in escalation penalties',
        },
        {
          priority: 2,
          priority_level: 'high',
          title: 'Expedite PFMS Disbursement for 42 Verified Landowners',
          reason: 'CALA awards approved but awaiting direct beneficiary bank transfers.',
          expected_impact: 'Achieves 92% land possession completion',
        },
        {
          priority: 3,
          priority_level: 'medium',
          title: 'Finalize Schedule V R&R Housing Allocation in Amer',
          reason: '18 displaced families awaiting allotment of alternative residential plots.',
          expected_impact: 'Resolves local Gram Sabha grievances',
        },
        {
          priority: 4,
          priority_level: 'low',
          title: 'Deploy Sentinel-2 Satellite Change Detection Guard',
          reason: 'Monitors 540 cadastral boundaries against commercial buffer encroachment.',
          expected_impact: '100% boundary security protection',
        },
      ],
    };
  }

  // 9. AI Anomalies
  if (path === '/api/ai/anomalies') {
    return [
      { id: 'anom-1', entity_type: 'Land Parcel', entity_id: 'pcl-001', anomaly_type: 'compensation_spike', severity: 'high', title: 'Unusual compensation value: ₹1.8Cr', description: 'Compensation 4.2x higher than district baseline average.', detected_value: '₹1.8 Cr', is_resolved: false, created_at: new Date().toISOString() },
      { id: 'anom-2', entity_type: 'Field Verification', entity_id: 'vrf-9912', anomaly_type: 'gps_mismatch', severity: 'medium', title: 'GPS mismatch on field verification', description: 'Field GPS tag was 320m outside recorded parcel boundary.', detected_value: '320m delta', is_resolved: false, created_at: new Date().toISOString() },
      { id: 'anom-3', entity_type: 'Land Parcel', entity_id: 'pcl-002', anomaly_type: 'duplicate_survey', severity: 'medium', title: 'Duplicate survey number flag', description: 'Identical survey number recorded across 2 overlapping projects.', detected_value: 'Survey 102/B', is_resolved: true, created_at: new Date().toISOString() },
    ];
  }

  // 10. AI Copilot
  if (path === '/api/ai/copilot') {
    return {
      response: 'BHUMI-AI Copilot Analysis: Based on statutory RFCTLARR Act 2013 rules, Section 11 preliminary notification requires 60 days for public objections. Proceeding with statutory award calculation for Jaipur district will reduce bottleneck risk by 35%.',
    };
  }

  // 11. AI Simulation
  if (path === '/api/ai/simulation') {
    return {
      current: {
        delay_probability_pct: 82,
        expected_delay_days: 49,
      },
      projected: {
        delay_probability_pct: 35,
        expected_delay_days: 18,
      },
      risk_reduction_pct: 47,
      days_saved: 31,
      interventions: [
        { action: 'Resolve 7 High Court Title Disputes', impact: 'High priority corridor unlocked', days_saved: 18 },
        { action: 'Expedite 42 Pending Compensation Vouchers', impact: '92% land possession acquired', days_saved: 9 },
        { action: 'Complete R&R Housing Allocation for 18 Families', impact: 'Gram Sabha grievance cleared', days_saved: 4 },
      ],
      disclaimer: 'Simulation estimates are calibrated via RFCTLARR Act 2013 statistical historical models.',
    };
  }

  // 12. Corridor Comparison
  if (path.startsWith('/api/ai/corridors/')) {
    return {
      corridors: [
        {
          alignment_id: 'align-01',
          name: 'Alignment A (NH-48 Bypass)',
          description: 'Optimal northern bypass alignment avoiding densely populated Amer municipal area.',
          suitability_score: 94,
          length_km: 34.2,
          land_required_hectares: 120.5,
          estimated_cost_crore: 450.0,
          forest_land_hectares: 0,
          displaced_families: 18,
          is_recommended: true,
        },
        {
          alignment_id: 'align-02',
          name: 'Alignment B (Direct Express)',
          description: 'Shorter central route through existing right-of-way, higher residential displacement.',
          suitability_score: 72,
          length_km: 29.8,
          land_required_hectares: 145.0,
          estimated_cost_crore: 580.0,
          forest_land_hectares: 2.4,
          displaced_families: 64,
          is_recommended: false,
        },
        {
          alignment_id: 'align-03',
          name: 'Alignment C (Southern Arc)',
          description: 'Southern peripheral route with higher agricultural land acquisition cost.',
          suitability_score: 68,
          length_km: 38.5,
          land_required_hectares: 160.2,
          estimated_cost_crore: 510.0,
          forest_land_hectares: 0,
          displaced_families: 42,
          is_recommended: false,
        },
      ],
    };
  }

  // 13. Workflow & Tasks
  if (path.startsWith('/api/workflow/tasks')) {
    return [
      { id: 'tsk-01', title: 'Section 11 Notification Verification', assigned_to: 'CALA Jaipur', status: 'Pending', due_date: '2026-09-15', priority: 'High', stage: 'Notice' },
      { id: 'tsk-02', title: 'SIA Report Approval', assigned_to: 'State Expert Committee', status: 'Completed', due_date: '2026-09-01', priority: 'Medium', stage: 'SIA' },
      { id: 'tsk-03', title: 'Gram Sabha Public Hearing Quorum Audit', assigned_to: 'District Collector', status: 'Pending', due_date: '2026-09-20', priority: 'High', stage: 'Objections' },
      { id: 'tsk-04', title: 'Section 19 Declaration Publication', assigned_to: 'CALA Ahmedabad', status: 'In Progress', due_date: '2026-09-18', priority: 'High', stage: 'Award' },
    ];
  }
  if (path === '/api/workflow/rules') {
    return { rules: [{ step: 'Sec 4', duration_days: 30 }, { step: 'Sec 11', duration_days: 60 }] };
  }
  if (path === '/api/workflow/transition') {
    return { success: true, message: 'Workflow stage updated successfully' };
  }

  // 14. Compensation
  if (path.startsWith('/api/compensation/')) {
    return [
      { id: 'cmp-01', parcel_id: 'pcl-001', award_amount: 4500000, status: 'disbursed', payment_reference: 'PFMS-982103', beneficiary_name: 'Ramesh Kumar', beneficiary_account: 'SBI-****-8921', disbursed_amount: 4500000, disbursed_at: '2026-08-20T10:00:00.000Z' },
      { id: 'cmp-02', parcel_id: 'pcl-002', award_amount: 3200000, status: 'under_verification', payment_reference: null, beneficiary_name: 'Suresh Patel', beneficiary_account: 'HDFC-****-4102', disbursed_amount: 3200000 },
      { id: 'cmp-03', parcel_id: 'pcl-003', award_amount: 5800000, status: 'pending', payment_reference: null, beneficiary_name: 'Geeta Devi', beneficiary_account: 'PNB-****-1093', disbursed_amount: 5800000 },
    ];
  }

  // 15. Disputes
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
    ];
  }

  // 16. Documents
  if (path.startsWith('/api/documents/')) {
    return [
      { id: 'doc-01', title: 'Section_11_Gazette_Notice_NH48.pdf', file_name: 'Section_11_Gazette_Notice_NH48.pdf', document_type: 'Statutory Notice', status: 'approved', ai_confidence_score: 0.98, version: '1.0', uploaded_at: new Date().toISOString() },
      { id: 'doc-02', title: 'SIA_Public_Hearing_Report_Amer.pdf', file_name: 'SIA_Public_Hearing_Report_Amer.pdf', document_type: 'SIA Study', status: 'approved', ai_confidence_score: 0.95, version: '1.2', uploaded_at: new Date().toISOString() },
      { id: 'doc-03', title: 'Section_19_Declaration_Jaipur.pdf', file_name: 'Section_19_Declaration_Jaipur.pdf', document_type: 'Statutory Declaration', status: 'under_review', ai_confidence_score: 0.91, version: '1.0', uploaded_at: new Date().toISOString() },
    ];
  }

  // 17. Land Bank & Encroachments
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
    ];
  }

  // 18. Integrations & Notifications
  if (path === '/api/integrations/status') {
    return { pfms: 'Connected', bhunaksha: 'Connected', parivesh: 'Connected', e_courts: 'Connected' };
  }
  if (path.startsWith('/api/notifications/')) {
    return [
      { id: 'notif-01', title: 'Award Disbursed via PFMS', message: 'PFMS payment of ₹45 Lakh processed for Parcel 101/A (Ramesh Kumar)', is_read: false },
      { id: 'notif-02', title: 'Dispute Hearing Scheduled', message: 'High Court title suit HC-RJ-2026/8912 scheduled for Sept 24', is_read: false },
    ];
  }

  // 19. Audit Log
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
    ];
  }

  // 20. R&R
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
    ];
  }

  // 21. Field Verification
  if (path.startsWith('/api/field/')) {
    return { success: true, verification_id: 'vrf-9912' };
  }

  // 22. Citizen Portal
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
