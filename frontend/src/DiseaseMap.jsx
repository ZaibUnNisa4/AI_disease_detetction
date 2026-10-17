import { useState, useMemo, useEffect, useRef } from 'react';

// Palette tokens aligned with PulseWatch medical design system
const PALETTE = {
  dengue: '#1d7862',        // Deep medical teal
  dengueBright: '#2ec4b6',  // Bright teal for pulse
  typhoid: '#d97706',       // Amber gold
  typhoidBright: '#f59e0b', // Bright amber for pulse
  critical: '#e11d48',      // Vivid crimson red
  alert: '#ea580c',         // Warning orange
  normal: '#059669',        // Stable emerald green
};

// Official CartoDB tile URLs with user's authorized API key
const CARTO_API_KEY = 'cb1_4n75_1_400c07ef8f30c90c1f64022b';
const CARTO_URLS = {
  voyager: `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=${CARTO_API_KEY}`,
  positron: `https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png?key=${CARTO_API_KEY}`,
  dark: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png?key=${CARTO_API_KEY}`
};

// Comprehensive nationwide dataset covering all provinces and administrative territories of Pakistan
const PAKISTAN_REGIONS = [
  // --- FEDERAL CAPITAL TERRITORY ---
  {
    id: "reg-isb",
    name: "Islamabad",
    province: "Federal Capital",
    latitude: 33.6844,
    longitude: 73.0479,
    primary_disease: "Dengue",
    secondary_disease: "Typhoid",
    risk_level: "Alert",
    z_score: 2.12,
    projected_cases: 145,
    case_change_pct: 8.4,
    status: "Pre-Epidemic Watch",
    dominant_vector: "Aedes aegypti",
    sentinel_hospitals: ["PIMS Islamabad", "Polyclinic Hospital (FGPC)", "Kulsum International"],
    population_at_risk_millions: 1.2,
    public_health_directive: "Larvicidal treatment of rainwater retention reservoirs; weekly community ovitrap monitoring in Sectors G-7, I-9, and Rawal Town.",
    transmission_index: 65
  },

  // --- PUNJAB PROVINCE ---
  {
    id: "reg-rwp",
    name: "Rawalpindi",
    province: "Punjab",
    latitude: 33.5973,
    longitude: 73.0479,
    primary_disease: "Dengue",
    secondary_disease: "Typhoid",
    risk_level: "Critical",
    z_score: 3.18,
    projected_cases: 432,
    case_change_pct: 24.5,
    status: "Active Outbreak",
    dominant_vector: "Aedes aegypti (Serotype DENV-2)",
    sentinel_hospitals: ["Holy Family Hospital", "Benazir Bhutto Hospital", "DHQ Rawalpindi"],
    population_at_risk_millions: 2.3,
    public_health_directive: "Intensify anti-larval indoor residual spraying in Potohar Town; establish 80-bed triage dengue isolation ward.",
    transmission_index: 88
  },
  {
    id: "reg-lhr",
    name: "Lahore",
    province: "Punjab",
    latitude: 31.5204,
    longitude: 74.3587,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Alert",
    z_score: 2.42,
    projected_cases: 310,
    case_change_pct: 12.1,
    status: "Elevated Surveillance",
    dominant_vector: "Salmonella Typhi & Aedes albopictus",
    sentinel_hospitals: ["Services Hospital Lahore", "Mayo Hospital", "Sir Ganga Ram Hospital"],
    population_at_risk_millions: 11.2,
    public_health_directive: "Audit sewage pipeline integrity in high-density union councils; mobilize mobile vector inspection teams.",
    transmission_index: 72
  },
  {
    id: "reg-fsd",
    name: "Faisalabad",
    province: "Punjab",
    latitude: 31.4504,
    longitude: 73.1350,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Alert",
    z_score: 2.08,
    projected_cases: 198,
    case_change_pct: 6.2,
    status: "Elevated Surveillance",
    dominant_vector: "Salmonella enterica",
    sentinel_hospitals: ["Allied Hospital Faisalabad", "DHQ Hospital Faisalabad"],
    population_at_risk_millions: 3.8,
    public_health_directive: "Public awareness advisories for water filtration and sanitation surveillance in peri-urban industrial belts.",
    transmission_index: 62
  },
  {
    id: "reg-mul",
    name: "Multan",
    province: "Punjab",
    latitude: 30.1575,
    longitude: 71.5249,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Alert",
    z_score: 2.15,
    projected_cases: 165,
    case_change_pct: 7.8,
    status: "Elevated Surveillance",
    dominant_vector: "Salmonella Typhi",
    sentinel_hospitals: ["Nishtar Hospital Multan", "Multan Institute of Cardiology"],
    population_at_risk_millions: 2.2,
    public_health_directive: "Enhance sanitation inspections around Southern Punjab peri-urban farming belts; distribute water chlorination tablets.",
    transmission_index: 64
  },
  {
    id: "reg-gjw",
    name: "Gujranwala",
    province: "Punjab",
    latitude: 32.1877,
    longitude: 74.1945,
    primary_disease: "Dengue",
    secondary_disease: "Typhoid",
    risk_level: "Alert",
    z_score: 2.20,
    projected_cases: 180,
    case_change_pct: 10.4,
    status: "Elevated Surveillance",
    dominant_vector: "Aedes aegypti",
    sentinel_hospitals: ["DHQ Teaching Hospital Gujranwala", "Gondal Medical Complex"],
    population_at_risk_millions: 2.4,
    public_health_directive: "Vector fogging in dense commercial auto bazaars and water vessel container inspections.",
    transmission_index: 68
  },
  {
    id: "reg-skt",
    name: "Sialkot",
    province: "Punjab",
    latitude: 32.4945,
    longitude: 74.5229,
    primary_disease: "Dengue",
    secondary_disease: "Typhoid",
    risk_level: "Alert",
    z_score: 2.05,
    projected_cases: 120,
    case_change_pct: 5.8,
    status: "Surveillance Watch",
    dominant_vector: "Aedes albopictus",
    sentinel_hospitals: ["Allama Iqbal Memorial Hospital", "Sardar Begum Teaching Hospital"],
    population_at_risk_millions: 1.7,
    public_health_directive: "Targeted indoor spraying in industrial export sectors and peri-urban water reservoirs.",
    transmission_index: 61
  },
  {
    id: "reg-bwp",
    name: "Bahawalpur",
    province: "Punjab",
    latitude: 29.3544,
    longitude: 71.6911,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Alert",
    z_score: 2.10,
    projected_cases: 110,
    case_change_pct: 6.5,
    status: "Elevated Surveillance",
    dominant_vector: "Salmonella Typhi",
    sentinel_hospitals: ["Bahawal Victoria Hospital", "Civil Hospital Bahawalpur"],
    population_at_risk_millions: 1.3,
    public_health_directive: "Safe drinking water supply audits and street food hygiene testing.",
    transmission_index: 63
  },
  {
    id: "reg-sgd",
    name: "Sargodha",
    province: "Punjab",
    latitude: 32.0836,
    longitude: 72.6711,
    primary_disease: "Dengue",
    secondary_disease: "Typhoid",
    risk_level: "Alert",
    z_score: 2.02,
    projected_cases: 95,
    case_change_pct: 4.2,
    status: "Seasonal Watch",
    dominant_vector: "Aedes aegypti",
    sentinel_hospitals: ["DHQ Teaching Hospital Sargodha"],
    population_at_risk_millions: 1.5,
    public_health_directive: "Citrus canal irrigation basin larva screening.",
    transmission_index: 58
  },
  {
    id: "reg-gjt",
    name: "Gujrat",
    province: "Punjab",
    latitude: 32.5742,
    longitude: 74.0754,
    primary_disease: "Dengue",
    secondary_disease: "Typhoid",
    risk_level: "Alert",
    z_score: 2.06,
    projected_cases: 88,
    case_change_pct: 5.1,
    status: "Elevated Surveillance",
    dominant_vector: "Aedes albopictus",
    sentinel_hospitals: ["Aziz Bhatti Shaheed Teaching Hospital"],
    population_at_risk_millions: 1.4,
    public_health_directive: "Chenab riverbank larva surveillance and ceramic factory audits.",
    transmission_index: 60
  },
  {
    id: "reg-ryk",
    name: "Rahim Yar Khan",
    province: "Punjab",
    latitude: 28.4212,
    longitude: 70.2989,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Alert",
    z_score: 2.12,
    projected_cases: 104,
    case_change_pct: 7.2,
    status: "Elevated Surveillance",
    dominant_vector: "Salmonella enterica",
    sentinel_hospitals: ["Sheikh Zayed Medical College & Hospital"],
    population_at_risk_millions: 1.6,
    public_health_directive: "Southern canal water decontamination and boiling awareness campaigns.",
    transmission_index: 64
  },
  {
    id: "reg-swl",
    name: "Sahiwal",
    province: "Punjab",
    latitude: 30.6682,
    longitude: 73.1114,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Normal",
    z_score: 1.32,
    projected_cases: 42,
    case_change_pct: 0.5,
    status: "Stable Baseline",
    dominant_vector: "Salmonella Typhi",
    sentinel_hospitals: ["Sahiwal Teaching Hospital"],
    population_at_risk_millions: 1.1,
    public_health_directive: "Periodic dairy belt tube-well water testing.",
    transmission_index: 34
  },

  // --- SINDH PROVINCE ---
  {
    id: "reg-khi",
    name: "Karachi",
    province: "Sindh",
    latitude: 24.8607,
    longitude: 67.0011,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Critical",
    z_score: 3.25,
    projected_cases: 785,
    case_change_pct: 19.8,
    status: "Severe Cluster (XDR)",
    dominant_vector: "Salmonella enterica serovar Typhi (H58 XDR clade)",
    sentinel_hospitals: ["Civil Hospital Karachi (Dr. Ruth Pfau)", "JPMC", "The Indus Hospital"],
    population_at_risk_millions: 16.8,
    public_health_directive: "Administer Typhoid Conjugate Vaccine (TCV); emergency chlorination of municipal water in Lyari, Korangi & Malir.",
    transmission_index: 94
  },
  {
    id: "reg-hyd",
    name: "Hyderabad",
    province: "Sindh",
    latitude: 25.3960,
    longitude: 68.3578,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Critical",
    z_score: 3.06,
    projected_cases: 275,
    case_change_pct: 15.6,
    status: "Active Outbreak",
    dominant_vector: "Salmonella enterica (Ceftriaxone-resistant)",
    sentinel_hospitals: ["Liaquat University Hospital", "Combined Military Hospital (CMH)"],
    population_at_risk_millions: 1.8,
    public_health_directive: "Issue urgent water boil advisory; dispatch mobile diagnostic clinics for rapid blood/stool culture sampling.",
    transmission_index: 86
  },
  {
    id: "reg-lrk",
    name: "Larkana",
    province: "Sindh",
    latitude: 27.5590,
    longitude: 68.2120,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Critical",
    z_score: 3.02,
    projected_cases: 190,
    case_change_pct: 17.2,
    status: "Active Outbreak (XDR)",
    dominant_vector: "Salmonella enterica (Multidrug-resistant)",
    sentinel_hospitals: ["Chandka Medical College Hospital", "SMBBMU Hospital"],
    population_at_risk_millions: 1.5,
    public_health_directive: "Mass antibiotic sensitivity surveillance and municipal water sterilization campaign.",
    transmission_index: 85
  },
  {
    id: "reg-skr",
    name: "Sukkur",
    province: "Sindh",
    latitude: 27.7052,
    longitude: 68.8574,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Alert",
    z_score: 2.14,
    projected_cases: 135,
    case_change_pct: 9.1,
    status: "Elevated Surveillance",
    dominant_vector: "Salmonella enterica",
    sentinel_hospitals: ["Ghulam Muhammad Mahar Medical College Hospital"],
    population_at_risk_millions: 1.2,
    public_health_directive: "Canal water filtration verification and community sanitary education.",
    transmission_index: 67
  },
  {
    id: "reg-mpk",
    name: "Mirpur Khas",
    province: "Sindh",
    latitude: 25.5276,
    longitude: 69.0125,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Alert",
    z_score: 2.09,
    projected_cases: 85,
    case_change_pct: 6.8,
    status: "Elevated Surveillance",
    dominant_vector: "Salmonella Typhi",
    sentinel_hospitals: ["Civil Hospital Mirpur Khas"],
    population_at_risk_millions: 0.9,
    public_health_directive: "Eastern agricultural canal water chlorination and enteric fever screening.",
    transmission_index: 61
  },
  {
    id: "reg-nwb",
    name: "Nawabshah",
    province: "Sindh",
    latitude: 26.2483,
    longitude: 68.4096,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Alert",
    z_score: 2.05,
    projected_cases: 78,
    case_change_pct: 4.8,
    status: "Surveillance Watch",
    dominant_vector: "Salmonella enterica",
    sentinel_hospitals: ["Peoples Medical College Hospital"],
    population_at_risk_millions: 0.8,
    public_health_directive: "School drinking water inspections and rapid widal/typhidot verification.",
    transmission_index: 59
  },
  {
    id: "reg-tha",
    name: "Thatta",
    province: "Sindh",
    latitude: 24.7474,
    longitude: 67.9235,
    primary_disease: "Dengue",
    secondary_disease: "Typhoid",
    risk_level: "Normal",
    z_score: 1.25,
    projected_cases: 32,
    case_change_pct: -1.5,
    status: "Coastal Baseline",
    dominant_vector: "Aedes aegypti",
    sentinel_hospitals: ["Civil Hospital Thatta"],
    population_at_risk_millions: 0.5,
    public_health_directive: "Coastal delta rainwater reservoir inspection.",
    transmission_index: 30
  },

  // --- KHYBER PAKHTUNKHWA PROVINCE ---
  {
    id: "reg-psh",
    name: "Peshawar",
    province: "Khyber Pakhtunkhwa",
    latitude: 34.0151,
    longitude: 71.5249,
    primary_disease: "Dengue",
    secondary_disease: "Typhoid",
    risk_level: "Normal",
    z_score: 1.48,
    projected_cases: 92,
    case_change_pct: -2.3,
    status: "Stable Baseline",
    dominant_vector: "Aedes albopictus",
    sentinel_hospitals: ["Lady Reading Hospital (LRH)", "Khyber Teaching Hospital (KTH)"],
    population_at_risk_millions: 2.1,
    public_health_directive: "Maintain standard community reporting and ovitrap counts; monitor post-monsoon tire shops and junkyards.",
    transmission_index: 38
  },
  {
    id: "reg-swt",
    name: "Swat",
    province: "Khyber Pakhtunkhwa",
    latitude: 34.7717,
    longitude: 72.3602,
    primary_disease: "Dengue",
    secondary_disease: "Typhoid",
    risk_level: "Normal",
    z_score: 1.22,
    projected_cases: 38,
    case_change_pct: -4.5,
    status: "Controlled Baseline",
    dominant_vector: "Aedes albopictus",
    sentinel_hospitals: ["Saidu Teaching Hospital"],
    population_at_risk_millions: 0.7,
    public_health_directive: "Seasonal stream bed checking and community education on domestic water vessel storage.",
    transmission_index: 28
  },
  {
    id: "reg-abt",
    name: "Abbottabad",
    province: "Khyber Pakhtunkhwa",
    latitude: 34.1688,
    longitude: 73.2215,
    primary_disease: "Dengue",
    secondary_disease: "Typhoid",
    risk_level: "Normal",
    z_score: 1.15,
    projected_cases: 29,
    case_change_pct: -1.2,
    status: "Controlled Baseline",
    dominant_vector: "Aedes albopictus",
    sentinel_hospitals: ["Ayub Teaching Hospital", "DHQ Hospital Abbottabad"],
    population_at_risk_millions: 0.8,
    public_health_directive: "Highland hill station larva survey and rainfall runoff surveillance.",
    transmission_index: 25
  },
  {
    id: "reg-mdn",
    name: "Mardan",
    province: "Khyber Pakhtunkhwa",
    latitude: 34.1989,
    longitude: 72.0404,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Normal",
    z_score: 1.35,
    projected_cases: 45,
    case_change_pct: 1.5,
    status: "Low Incidence",
    dominant_vector: "Salmonella enterica",
    sentinel_hospitals: ["Mardan Medical Complex (MMC)"],
    population_at_risk_millions: 1.0,
    public_health_directive: "Periodic water testing in public schools and peri-urban tube wells.",
    transmission_index: 33
  },
  {
    id: "reg-dik",
    name: "Dera Ismail Khan",
    province: "Khyber Pakhtunkhwa",
    latitude: 31.8314,
    longitude: 70.9019,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Alert",
    z_score: 2.08,
    projected_cases: 72,
    case_change_pct: 8.2,
    status: "Elevated Surveillance",
    dominant_vector: "Salmonella Typhi",
    sentinel_hospitals: ["DHQ Teaching Hospital DI Khan", "Mufti Mehmood Memorial Hospital"],
    population_at_risk_millions: 0.9,
    public_health_directive: "Indus riverbank water pump chlorination and flood residue sanitary treatment.",
    transmission_index: 62
  },
  {
    id: "reg-kht",
    name: "Kohat",
    province: "Khyber Pakhtunkhwa",
    latitude: 33.5869,
    longitude: 71.4414,
    primary_disease: "Dengue",
    secondary_disease: "Typhoid",
    risk_level: "Normal",
    z_score: 1.28,
    projected_cases: 36,
    case_change_pct: 1.1,
    status: "Stable Baseline",
    dominant_vector: "Aedes albopictus",
    sentinel_hospitals: ["KDA District Teaching Hospital Kohat"],
    population_at_risk_millions: 0.6,
    public_health_directive: "Ovitrap surveillance in urban tunnel highway corridor.",
    transmission_index: 29
  },

  // --- BALOCHISTAN PROVINCE ---
  {
    id: "reg-que",
    name: "Quetta",
    province: "Balochistan",
    latitude: 30.1798,
    longitude: 66.9750,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Normal",
    z_score: 1.18,
    projected_cases: 54,
    case_change_pct: 1.2,
    status: "Low Incidence",
    dominant_vector: "Salmonella enterica",
    sentinel_hospitals: ["Bolan Medical Complex Hospital", "Sandeman Provincial Hospital"],
    population_at_risk_millions: 1.1,
    public_health_directive: "Periodic sanitary inspection of urban water supply lines and public karez channels.",
    transmission_index: 31
  },
  {
    id: "reg-gwd",
    name: "Gwadar",
    province: "Balochistan",
    latitude: 25.1264,
    longitude: 62.3225,
    primary_disease: "Dengue",
    secondary_disease: "Typhoid",
    risk_level: "Normal",
    z_score: 1.05,
    projected_cases: 22,
    case_change_pct: 0.8,
    status: "Coastal Baseline",
    dominant_vector: "Aedes aegypti",
    sentinel_hospitals: ["GDA Hospital Gwadar", "DHQ Hospital Gwadar"],
    population_at_risk_millions: 0.3,
    public_health_directive: "Desalination water vessel storage inspections and boat dock larvicide treatment.",
    transmission_index: 24
  },
  {
    id: "reg-kzd",
    name: "Khuzdar",
    province: "Balochistan",
    latitude: 27.8119,
    longitude: 66.6053,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Normal",
    z_score: 1.12,
    projected_cases: 28,
    case_change_pct: 0.2,
    status: "Low Incidence",
    dominant_vector: "Salmonella enterica",
    sentinel_hospitals: ["Teaching Hospital Khuzdar"],
    population_at_risk_millions: 0.4,
    public_health_directive: "Inland well water testing and boiling hygiene education.",
    transmission_index: 26
  },
  {
    id: "reg-trb",
    name: "Turbat",
    province: "Balochistan",
    latitude: 26.0081,
    longitude: 63.0494,
    primary_disease: "Dengue",
    secondary_disease: "Typhoid",
    risk_level: "Normal",
    z_score: 1.16,
    projected_cases: 31,
    case_change_pct: 1.8,
    status: "Seasonal Watch",
    dominant_vector: "Aedes aegypti",
    sentinel_hospitals: ["DHQ Teaching Hospital Turbat"],
    population_at_risk_millions: 0.4,
    public_health_directive: "Kech river oasis ovitrap checks and household water vessel larvicide.",
    transmission_index: 27
  },

  // --- AZAD JAMMU & KASHMIR (AJK) ---
  {
    id: "reg-mzf",
    name: "Muzaffarabad",
    province: "Azad Jammu & Kashmir",
    latitude: 34.3597,
    longitude: 73.4711,
    primary_disease: "Dengue",
    secondary_disease: "Typhoid",
    risk_level: "Normal",
    z_score: 1.10,
    projected_cases: 25,
    case_change_pct: -3.1,
    status: "Controlled Baseline",
    dominant_vector: "Aedes albopictus",
    sentinel_hospitals: ["AIMS Muzaffarabad", "CMH Muzaffarabad"],
    population_at_risk_millions: 0.6,
    public_health_directive: "Neelum & Jhelum confluence larva surveys and seasonal tourist advisory.",
    transmission_index: 26
  },
  {
    id: "reg-mrp",
    name: "Mirpur",
    province: "Azad Jammu & Kashmir",
    latitude: 33.1484,
    longitude: 73.7519,
    primary_disease: "Dengue",
    secondary_disease: "Typhoid",
    risk_level: "Alert",
    z_score: 2.04,
    projected_cases: 64,
    case_change_pct: 6.4,
    status: "Surveillance Watch",
    dominant_vector: "Aedes albopictus",
    sentinel_hospitals: ["Divisional Headquarter Hospital Mirpur"],
    population_at_risk_millions: 0.5,
    public_health_directive: "Mangla dam rim reservoir ovitrap counts and residential larvicide.",
    transmission_index: 59
  },

  // --- GILGIT-BALTISTAN ---
  {
    id: "reg-glt",
    name: "Gilgit",
    province: "Gilgit-Baltistan",
    latitude: 35.9221,
    longitude: 74.3087,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Normal",
    z_score: 0.95,
    projected_cases: 18,
    case_change_pct: -2.0,
    status: "Low Incidence",
    dominant_vector: "Salmonella enterica",
    sentinel_hospitals: ["DHQ Hospital Gilgit", "City Hospital Gilgit"],
    population_at_risk_millions: 0.4,
    public_health_directive: "Glacial meltwater source sanitation audits and community boiling advisories.",
    transmission_index: 20
  },
  {
    id: "reg-skd",
    name: "Skardu",
    province: "Gilgit-Baltistan",
    latitude: 35.2971,
    longitude: 75.6333,
    primary_disease: "Typhoid",
    secondary_disease: "Dengue",
    risk_level: "Normal",
    z_score: 0.88,
    projected_cases: 14,
    case_change_pct: -1.0,
    status: "Low Incidence",
    dominant_vector: "Salmonella enterica",
    sentinel_hospitals: ["DHQ Hospital Skardu"],
    population_at_risk_millions: 0.3,
    public_health_directive: "High-altitude spring water testing and winter food sanitation.",
    transmission_index: 18
  }
];

// Coordinates projection calibrated strictly to the full geographical bounds of Pakistan
const GEO_BOUNDS = {
  minLon: 60.5,
  maxLon: 77.8,
  minLat: 23.4,
  maxLat: 37.4,
  width: 900,
  height: 800,
  paddingX: 40,
  paddingY: 35
};

function projectCoords(lat, lon) {
  const { minLon, maxLon, minLat, maxLat, width, height, paddingX, paddingY } = GEO_BOUNDS;
  const usableW = width - (paddingX * 2);
  const usableH = height - (paddingY * 2);

  const x = paddingX + ((lon - minLon) / (maxLon - minLon)) * usableW;
  const y = paddingY + ((maxLat - lat) / (maxLat - minLat)) * usableH;
  return { x: Math.round(x * 10) / 10, y: Math.round(y * 10) / 10 };
}

export default function DiseaseMap({ apiBase, onSelectForScreening, onRequestRefresh }) {
  const [regions, setRegions] = useState(PAKISTAN_REGIONS);
  const [loading, setLoading] = useState(false);
  
  // Interactive filters
  const [diseaseFilter, setDiseaseFilter] = useState('ALL'); // 'ALL' | 'Dengue' | 'Typhoid'
  const [riskFilter, setRiskFilter] = useState('ALL');       // 'ALL' | 'Critical' | 'Alert' | 'Normal'
  const [provinceFilter, setProvinceFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Display modes: 'tiles' (OpenStreetMap/Carto) | 'vector' (SVG National GIS) | 'radar'
  const [mapType, setMapType] = useState('tiles');          // 'tiles' | 'vector'
  const [cartoStyle, setCartoStyle] = useState('voyager');   // 'voyager' | 'positron' | 'dark'
  const [viewMode, setViewMode] = useState('radar');         // 'radar' | 'vector' | 'hospitals'
  const [isExpanded, setIsExpanded] = useState(false);       // Fullscreen / Expanded full map mode
  const [drawerOpen, setDrawerOpen] = useState(true);
  
  // Selected region
  const [selectedId, setSelectedId] = useState('reg-rwp');
  const [hoveredRegion, setHoveredRegion] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const mapContainerRef = useRef(null);
  const leafletMapRef = useRef(null);
  const leafletInstanceRef = useRef(null);
  const tileLayerRef = useRef(null);
  const markersGroupRef = useRef(null);

  // Fetch latest backend surveillance regions
  const fetchRegions = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/surveillance/regions`);
      if (res.ok) {
        const data = await res.json();
        if (data && Array.isArray(data.regions) && data.regions.length > 0) {
          // Merge API data with PAKISTAN_REGIONS so full coverage is preserved
          const existingIds = new Set(data.regions.map(r => r.id));
          const extra = PAKISTAN_REGIONS.filter(r => !existingIds.has(r.id));
          setRegions([...data.regions, ...extra]);
        }
      }
    } catch (err) {
      console.warn('API surveillance fetch error, using full nationwide dataset:', err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRegions();
  }, [apiBase]);

  // Unique provinces list
  const provinces = useMemo(() => {
    const list = Array.from(new Set(regions.map(r => r.province).filter(Boolean)));
    return list.sort();
  }, [regions]);

  // Filtered regions
  const filteredRegions = useMemo(() => {
    return regions.filter(r => {
      // Disease filter
      if (diseaseFilter !== 'ALL') {
        const matchesPrimary = r.primary_disease.toLowerCase() === diseaseFilter.toLowerCase();
        if (!matchesPrimary) return false;
      }
      // Risk filter
      if (riskFilter !== 'ALL' && r.risk_level.toLowerCase() !== riskFilter.toLowerCase()) {
        return false;
      }
      // Province filter
      if (provinceFilter !== 'ALL' && r.province !== provinceFilter) {
        return false;
      }
      // Search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const inName = r.name.toLowerCase().includes(q);
        const inProv = r.province.toLowerCase().includes(q);
        const inVec = (r.dominant_vector || '').toLowerCase().includes(q);
        const inHosp = (r.sentinel_hospitals || []).some(h => h.toLowerCase().includes(q));
        if (!inName && !inProv && !inVec && !inHosp) return false;
      }
      return true;
    });
  }, [regions, diseaseFilter, riskFilter, provinceFilter, searchQuery]);

  // Currently selected region
  const activeRegion = useMemo(() => {
    return regions.find(r => r.id === selectedId) || filteredRegions[0] || regions[0];
  }, [regions, selectedId, filteredRegions]);

  // Summary Metrics
  const metrics = useMemo(() => {
    const total = regions.length;
    const dengueCount = regions.filter(r => r.primary_disease === 'Dengue').length;
    const typhoidCount = regions.filter(r => r.primary_disease === 'Typhoid').length;
    const criticalCount = regions.filter(r => r.risk_level === 'Critical').length;
    const alertCount = regions.filter(r => r.risk_level === 'Alert').length;
    const dengueCases = regions.filter(r => r.primary_disease === 'Dengue').reduce((s, r) => s + (r.projected_cases || 0), 0);
    const typhoidCases = regions.filter(r => r.primary_disease === 'Typhoid').reduce((s, r) => s + (r.projected_cases || 0), 0);
    const totalCases = regions.reduce((s, r) => s + (r.projected_cases || 0), 0);
    const totalPop = regions.reduce((s, r) => s + (r.population_at_risk_millions || 0), 0).toFixed(1);

    return { total, dengueCount, typhoidCount, criticalCount, alertCount, dengueCases, typhoidCases, totalCases, totalPop };
  }, [regions]);

  // Initialize or update Leaflet Map when in 'tiles' mode
  useEffect(() => {
    if (mapType !== 'tiles' || !leafletMapRef.current) return;

    const L = window.L;
    if (!L) {
      console.warn('Leaflet library not yet loaded in window. Falling back to SVG vector view.');
      setMapType('vector');
      return;
    }

    // Initialize Leaflet Map if not created
    if (!leafletInstanceRef.current) {
      const map = L.map(leafletMapRef.current, {
        center: [30.3753, 69.3451], // Center of Pakistan
        zoom: 5.6,
        minZoom: 5,
        maxZoom: 13,
        zoomControl: true,
        attributionControl: false
      });

      // CartoDB tiles with user's authorized API key
      tileLayerRef.current = L.tileLayer(CARTO_URLS[cartoStyle], {
        maxZoom: 19,
        subdomains: 'abcd',
        attribution: '&copy; CARTO &copy; OpenStreetMap contributors'
      }).addTo(map);

      // Fit strictly to Pakistan bounds
      map.fitBounds([
        [23.5, 60.5], // South-West (Gwadar / Arabian Sea)
        [37.2, 77.5]  // North-East (Khunjerab / Gilgit-Baltistan)
      ]);

      markersGroupRef.current = L.layerGroup().addTo(map);
      leafletInstanceRef.current = map;
    }

    // Dynamic style update if tile layer is already mounted
    if (tileLayerRef.current && CARTO_URLS[cartoStyle]) {
      tileLayerRef.current.setUrl(CARTO_URLS[cartoStyle]);
    }

    // Update markers on the map
    if (markersGroupRef.current) {
      markersGroupRef.current.clearLayers();

      filteredRegions.forEach(r => {
        const isCritical = r.risk_level === 'Critical';
        const isDengue = r.primary_disease === 'Dengue';
        const isSelected = r.id === activeRegion?.id;
        const color = isCritical ? PALETTE.critical : isDengue ? PALETTE.dengue : PALETTE.typhoid;

        // Custom HTML marker for Leaflet
        const iconHtml = `
          <div class="leaflet-custom-marker ${isSelected ? 'selected' : ''} ${isCritical ? 'critical' : ''}">
            ${isCritical ? '<div class="leaflet-pulse-ring"></div>' : ''}
            <div class="leaflet-marker-core" style="background:${color}">
              <span>${isDengue ? '🦟' : '🧫'}</span>
            </div>
            <div class="leaflet-marker-label">${r.name}</div>
          </div>
        `;

        const customIcon = L.divIcon({
          html: iconHtml,
          className: 'leaflet-marker-wrapper',
          iconSize: [36, 36],
          iconAnchor: [18, 18]
        });

        const marker = L.marker([r.latitude, r.longitude], { icon: customIcon });

        // Popup content
        const popupContent = `
          <div class="leaflet-popup-card">
            <h4>${r.name} (${r.province})</h4>
            <div class="popup-disease-tag ${r.primary_disease.toLowerCase()}">
              ${isDengue ? '🦟 Dengue' : '🧫 Typhoid'} · ${r.risk_level} Risk
            </div>
            <div class="popup-stats">
              <div>Projected Cases: <b>${r.projected_cases}</b></div>
              <div>Anomaly Z-Score: <b>Z ${Number(r.z_score).toFixed(2)}</b></div>
              <div>Vector: <small>${r.dominant_vector}</small></div>
            </div>
          </div>
        `;

        marker.bindPopup(popupContent);
        marker.on('click', () => {
          setSelectedId(r.id);
        });

        markersGroupRef.current.addLayer(marker);
      });
    }

    // Invalidate size on container resize
    setTimeout(() => {
      leafletInstanceRef.current?.invalidateSize();
    }, 150);

  }, [mapType, filteredRegions, activeRegion, isExpanded]);

  // Center Leaflet map when a region is selected
  useEffect(() => {
    if (mapType === 'tiles' && leafletInstanceRef.current && activeRegion) {
      leafletInstanceRef.current.panTo([activeRegion.latitude, activeRegion.longitude], {
        animate: true,
        duration: 0.8
      });
    }
  }, [activeRegion, mapType]);

  const handleMarkerHover = (r, e) => {
    setHoveredRegion(r);
    if (mapContainerRef.current) {
      const rect = mapContainerRef.current.getBoundingClientRect();
      setTooltipPos({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      });
    }
  };

  const handleMarkerLeave = () => {
    setHoveredRegion(null);
  };

  const resetFullMap = () => {
    if (leafletInstanceRef.current) {
      leafletInstanceRef.current.fitBounds([
        [23.5, 60.5],
        [37.2, 77.5]
      ]);
    }
  };

  return (
    <div className={`disease-map-page ${isExpanded ? 'fullscreen-mode' : ''}`}>
      {/* Top Header */}
      <div className="heading map-header">
        <div>
          <div className="eyebrow">National Epidemiological Surveillance GIS</div>
          <h1>Full Disease Outbreak Map of Pakistan</h1>
          <p>
            Complete geographical coverage across all 7 provinces and administrative territories of Pakistan. 
            Real-time tracking of <strong>Dengue vectors</strong> (<em>Aedes aegypti / albopictus</em>) and <strong>Typhoid clusters</strong> (<em>Salmonella Typhi H58 XDR</em>).
          </p>
        </div>
        <div className="map-top-actions">
          <button
            className={`btn ${isExpanded ? 'primary' : ''}`}
            onClick={() => setIsExpanded(!isExpanded)}
            title="Expand to Full Width / Fullscreen View"
          >
            {isExpanded ? '⛶ Collapse View' : '⛶ Expand Full Map'}
          </button>
          <button className="btn" onClick={fetchRegions} disabled={loading} title="Re-sync data">
            {loading ? '↻ Updating…' : '↻ Refresh Map'}
          </button>
        </div>
      </div>

      {/* Top Metrics Ribbon */}
      <div className="metrics map-metrics-grid">
        <article className="card metric map-metric-card">
          <div>Total Monitored Areas <i>🇵🇰</i></div>
          <strong>{metrics.total} <span className="metric-sub">Districts</span></strong>
          <small>All provinces & territories covered</small>
        </article>

        <article className="card metric map-metric-card dengue-metric">
          <div>Dengue Affected Areas <i className="dengue-icon">🦟</i></div>
          <strong>{metrics.dengueCount} <span className="metric-sub">Districts</span></strong>
          <small>{metrics.dengueCases.toLocaleString()} projected cases</small>
        </article>

        <article className="card metric map-metric-card typhoid-metric">
          <div>Typhoid Affected Areas <i className="typhoid-icon">🧫</i></div>
          <strong>{metrics.typhoidCount} <span className="metric-sub">Districts</span></strong>
          <small>{metrics.typhoidCases.toLocaleString()} projected cases</small>
        </article>

        <article className="card metric map-metric-card critical-metric">
          <div>Critical Outbreak Hotspots <i className="amber">♢</i></div>
          <strong className="text-critical">{metrics.criticalCount} <span className="metric-sub">Epicenters</span></strong>
          <small>Rawalpindi · Karachi · Hyderabad · Larkana</small>
        </article>

        <article className="card metric map-metric-card pop-metric">
          <div>Exposed Population <i>👥</i></div>
          <strong>{metrics.totalPop} M</strong>
          <small>National high-risk zone</small>
        </article>
      </div>

      {/* Main Filter & Layer Toolbar */}
      <div className="card map-toolbar-card">
        {/* Map Type Switcher */}
        <div className="toolbar-group">
          <span className="toolbar-label">Map Engine:</span>
          <div className="pill-toggle-group">
            <button
              className={`pill-btn ${mapType === 'tiles' ? 'active' : ''}`}
              onClick={() => setMapType('tiles')}
              title="CartoDB full Pakistan map powered by official API key"
            >
              🗺️ Full Tile Map
            </button>
            <button
              className={`pill-btn ${mapType === 'vector' ? 'active' : ''}`}
              onClick={() => setMapType('vector')}
              title="High-precision SVG National GIS vector map"
            >
              ◎ National Vector GIS
            </button>
          </div>
        </div>

        {/* Carto Style Selector when in Tile Map mode */}
        {mapType === 'tiles' && (
          <div className="toolbar-group">
            <span className="toolbar-label">Carto Style:</span>
            <div className="pill-toggle-group">
              <button
                className={`pill-btn ${cartoStyle === 'voyager' ? 'active' : ''}`}
                onClick={() => setCartoStyle('voyager')}
                title="Carto Voyager Colorful Map"
              >
                Voyager
              </button>
              <button
                className={`pill-btn ${cartoStyle === 'positron' ? 'active' : ''}`}
                onClick={() => setCartoStyle('positron')}
                title="Carto Positron Clean Light Medical Style"
              >
                Positron (Light)
              </button>
              <button
                className={`pill-btn ${cartoStyle === 'dark' ? 'active' : ''}`}
                onClick={() => setCartoStyle('dark')}
                title="Carto Dark Matter Night Map"
              >
                Dark Matter
              </button>
            </div>
          </div>
        )}

        {/* Disease Filter */}
        <div className="toolbar-group">
          <span className="toolbar-label">Affected Disease:</span>
          <div className="pill-toggle-group">
            <button
              className={`pill-btn ${diseaseFilter === 'ALL' ? 'active' : ''}`}
              onClick={() => setDiseaseFilter('ALL')}
            >
              All Diseases ({regions.length})
            </button>
            <button
              className={`pill-btn dengue ${diseaseFilter === 'Dengue' ? 'active' : ''}`}
              onClick={() => setDiseaseFilter('Dengue')}
            >
              <span className="pill-dot dengue-dot"></span> Dengue ({metrics.dengueCount})
            </button>
            <button
              className={`pill-btn typhoid ${diseaseFilter === 'Typhoid' ? 'active' : ''}`}
              onClick={() => setDiseaseFilter('Typhoid')}
            >
              <span className="pill-dot typhoid-dot"></span> Typhoid ({metrics.typhoidCount})
            </button>
          </div>
        </div>

        {/* Risk Level Filter */}
        <div className="toolbar-group">
          <span className="toolbar-label">Severity:</span>
          <div className="pill-toggle-group">
            {['ALL', 'Critical', 'Alert', 'Normal'].map(level => (
              <button
                key={level}
                className={`pill-btn ${riskFilter === level ? 'active' : ''} ${level.toLowerCase()}`}
                onClick={() => setRiskFilter(level)}
              >
                {level === 'ALL' ? 'All Severities' : level}
              </button>
            ))}
          </div>
        </div>

        {/* Province Filter */}
        <div className="toolbar-group">
          <span className="toolbar-label">Province:</span>
          <select
            className="map-select"
            value={provinceFilter}
            onChange={e => setProvinceFilter(e.target.value)}
          >
            <option value="ALL">All Pakistan Provinces & Territories</option>
            {provinces.map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>

        {/* Search Input */}
        <div className="toolbar-group search-group">
          <input
            type="text"
            className="search map-search"
            placeholder="⌕ Search any city or district of Pakistan…"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button className="clear-search-btn" onClick={() => setSearchQuery('')}>×</button>
          )}
        </div>
      </div>

      {/* Quick Epicenter Focus Bar */}
      <div className="quick-epicenter-bar">
        <span className="quick-label">⚡ Direct Focus Epicenter:</span>
        <button
          className="epicenter-chip critical-chip"
          onClick={() => { setSelectedId('reg-rwp'); setDiseaseFilter('Dengue'); }}
        >
          🔥 Rawalpindi · Dengue Outbreak (432 cases)
        </button>
        <button
          className="epicenter-chip critical-chip"
          onClick={() => { setSelectedId('reg-khi'); setDiseaseFilter('Typhoid'); }}
        >
          ⚠️ Karachi · Typhoid XDR Hotspot (785 cases)
        </button>
        <button
          className="epicenter-chip critical-chip"
          onClick={() => { setSelectedId('reg-hyd'); setDiseaseFilter('Typhoid'); }}
        >
          📍 Hyderabad · Resistant Typhoid (275 cases)
        </button>
        <button
          className="epicenter-chip alert-chip"
          onClick={() => { setSelectedId('reg-lhr'); setDiseaseFilter('ALL'); }}
        >
          📍 Lahore · Dual Surveillance (310 cases)
        </button>
        <button
          className="epicenter-chip alert-chip"
          onClick={() => { setSelectedId('reg-isb'); setDiseaseFilter('Dengue'); }}
        >
          📍 Islamabad · Federal Watch (145 cases)
        </button>
        <button
          className="epicenter-chip"
          onClick={resetFullMap}
        >
          🇵🇰 Center Full Pakistan View
        </button>
      </div>

      {/* Main Map Workspace Layout */}
      <div className={`map-workspace-grid ${isExpanded ? 'expanded-layout' : ''}`}>
        {/* Left Map Viewport */}
        <div className="card map-viewport-card" ref={mapContainerRef}>
          <div className="map-viewport-head">
            <div className="map-title-wrap">
              <h2>
                {mapType === 'tiles' ? 'Full Map of Pakistan · Interactive Tile View' : 'Pakistan National GIS Vector Map'}
              </h2>
              <p>
                Showing {filteredRegions.length} districts · Showing transmission vectors, Z-scores, and sentinel networks
              </p>
            </div>

            {/* View Mode Controls */}
            <div className="view-mode-tabs">
              <button
                className={`mode-btn ${viewMode === 'radar' ? 'active' : ''}`}
                onClick={() => setViewMode('radar')}
              >
                ◎ Outbreak Radar
              </button>
              <button
                className={`mode-btn ${viewMode === 'vector' ? 'active' : ''}`}
                onClick={() => setViewMode('vector')}
              >
                🦟 Vector Clades
              </button>
              <button
                className={`mode-btn ${viewMode === 'hospitals' ? 'active' : ''}`}
                onClick={() => setViewMode('hospitals')}
              >
                🏥 Sentinels
              </button>
              {isExpanded && (
                <button
                  className={`mode-btn ${drawerOpen ? 'active' : ''}`}
                  onClick={() => setDrawerOpen(!drawerOpen)}
                >
                  📋 {drawerOpen ? 'Hide Dossier' : 'Show Dossier'}
                </button>
              )}
            </div>
          </div>

          {/* Map Body: Either Leaflet Tile Map or High-Precision SVG Vector Map */}
          {mapType === 'tiles' ? (
            <div className="leaflet-map-wrapper">
              <div id="pakistan-leaflet-map" ref={leafletMapRef} className="leaflet-canvas"></div>
              {/* Overlay Legend */}
              <div className="leaflet-floating-legend">
                <span className="legend-title">OUTBREAK LEGEND</span>
                <div><span className="legend-dot dengue"></span> Dengue (Aedes)</div>
                <div><span className="legend-dot typhoid"></span> Typhoid (Salmonella)</div>
                <div><span className="legend-dot critical"></span> Critical Hotspot ($Z \ge 3.0$)</div>
              </div>
            </div>
          ) : (
            <div className="svg-map-container">
              <svg
                viewBox="0 0 900 800"
                className="pakistan-map-svg"
                aria-label="Full Map of Pakistan displaying infectious disease transmission"
              >
                <defs>
                  <radialGradient id="grad-dengue" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#2ec4b6" stopOpacity="0.9" />
                    <stop offset="60%" stopColor="#1d7862" stopOpacity="0.75" />
                    <stop offset="100%" stopColor="#1d7862" stopOpacity="0.1" />
                  </radialGradient>
                  <radialGradient id="grad-typhoid" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.9" />
                    <stop offset="60%" stopColor="#d97706" stopOpacity="0.75" />
                    <stop offset="100%" stopColor="#d97706" stopOpacity="0.1" />
                  </radialGradient>
                  <radialGradient id="grad-critical" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.95" />
                    <stop offset="60%" stopColor="#e11d48" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#e11d48" stopOpacity="0.15" />
                  </radialGradient>
                  <filter id="spotlight-glow" x="-50%" y="-50%" width="200%" height="200%">
                    <feDropShadow dx="0" dy="0" stdDeviation="6" floodColor="#ffffff" floodOpacity="0.9" />
                  </filter>
                  <filter id="marker-shadow" x="-30%" y="-30%" width="160%" height="160%">
                    <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#0d241e" floodOpacity="0.35" />
                  </filter>
                </defs>

                {/* Coordinate Grid Layer */}
                <g className="map-grid-layer" opacity="0.4">
                  <line x1="40" y1="130" x2="860" y2="130" stroke="#d5ddd7" strokeDasharray="3 3" />
                  <text x="50" y="125" className="grid-label">36° N (Gilgit-Baltistan / Karakoram)</text>
                  
                  <line x1="40" y1="310" x2="860" y2="310" stroke="#d5ddd7" strokeDasharray="3 3" />
                  <text x="50" y="305" className="grid-label">32° N (Punjab / KPK)</text>

                  <line x1="40" y1="490" x2="860" y2="490" stroke="#d5ddd7" strokeDasharray="3 3" />
                  <text x="50" y="485" className="grid-label">28° N (Balochistan / Upper Sindh)</text>

                  <line x1="40" y1="670" x2="860" y2="670" stroke="#d5ddd7" strokeDasharray="3 3" />
                  <text x="50" y="665" className="grid-label">24° N (Karachi / Arabian Sea Coast)</text>

                  <line x1="180" y1="50" x2="180" y2="760" stroke="#d5ddd7" strokeDasharray="3 3" />
                  <text x="185" y="775" className="grid-label">64° E</text>

                  <line x1="420" y1="50" x2="420" y2="760" stroke="#d5ddd7" strokeDasharray="3 3" />
                  <text x="425" y="775" className="grid-label">68° E</text>

                  <line x1="660" y1="50" x2="660" y2="760" stroke="#d5ddd7" strokeDasharray="3 3" />
                  <text x="665" y="775" className="grid-label">72° E</text>
                </g>

                {/* Full Pakistan Provincial Outline Polygons */}
                <g className="provinces-layer">
                  {/* Balochistan (South-West) */}
                  <path
                    d="M 90,690 L 70,640 L 75,520 L 140,460 L 200,420 L 320,410 L 400,440 L 440,520 L 420,620 L 350,680 L 220,700 Z"
                    className="province-polygon balochistan"
                    title="Balochistan Province"
                  />
                  <text x="210" y="550" className="province-watermark">BALOCHISTAN</text>

                  {/* Sindh (South-East) */}
                  <path
                    d="M 350,680 L 420,620 L 440,520 L 510,510 L 560,570 L 570,670 L 480,720 L 380,710 Z"
                    className="province-polygon sindh"
                    title="Sindh Province"
                  />
                  <text x="460" y="620" className="province-watermark">SINDH</text>

                  {/* Punjab (Central-East) */}
                  <path
                    d="M 400,440 L 320,410 L 360,340 L 470,310 L 570,300 L 670,310 L 690,390 L 630,480 L 510,510 L 440,520 Z"
                    className="province-polygon punjab"
                    title="Punjab Province"
                  />
                  <text x="500" y="410" className="province-watermark">PUNJAB</text>

                  {/* Khyber Pakhtunkhwa (North-West) */}
                  <path
                    d="M 360,340 L 320,410 L 270,350 L 290,250 L 400,190 L 480,160 L 520,210 L 470,310 Z"
                    className="province-polygon kpk"
                    title="Khyber Pakhtunkhwa"
                  />
                  <text x="370" y="260" className="province-watermark">KPK</text>

                  {/* Gilgit-Baltistan (Far North) */}
                  <path
                    d="M 480,160 L 400,190 L 440,110 L 530,70 L 680,80 L 730,140 L 630,190 L 520,210 Z"
                    className="province-polygon gilgit"
                    title="Gilgit-Baltistan"
                  />
                  <text x="550" y="140" className="province-watermark">GILGIT-BALTISTAN</text>

                  {/* Azad Jammu & Kashmir (North-East) */}
                  <path
                    d="M 520,210 L 630,190 L 690,250 L 670,310 L 570,300 Z"
                    className="province-polygon ajk"
                    title="Azad Jammu & Kashmir"
                  />
                  <text x="600" y="260" className="province-watermark">AJK</text>

                  {/* Arabian Sea Coastline */}
                  <path
                    d="M 60,700 Q 210,710 350,685 Q 430,730 570,690"
                    fill="none"
                    stroke="#8ac4b4"
                    strokeWidth="3.5"
                    strokeLinecap="round"
                  />
                  <text x="180" y="735" className="sea-watermark">ARABIAN SEA (SURVEILLANCE COASTLINE)</text>

                  {/* Indus River System (Major Waterborne Vector Highway) */}
                  <path
                    d="M 570,110 Q 500,200 460,310 T 450,470 T 410,640 T 390,700"
                    fill="none"
                    stroke="#98d2c2"
                    strokeWidth="2.8"
                    strokeDasharray="6 3"
                    opacity="0.8"
                  />
                </g>

                {/* Markers Layer for All Districts */}
                <g className="markers-layer">
                  {filteredRegions.map(r => {
                    const pt = projectCoords(r.latitude, r.longitude);
                    const isSelected = r.id === activeRegion?.id;
                    const isCritical = r.risk_level === 'Critical';
                    const isAlert = r.risk_level === 'Alert';
                    const isDengue = r.primary_disease === 'Dengue';

                    const baseRadius = isCritical ? 15 : isAlert ? 12 : 9;
                    const caseBonus = Math.min(8, Math.max(0, Math.log10(r.projected_cases || 10) * 3));
                    const markerRadius = baseRadius + caseBonus;

                    const color = isCritical ? PALETTE.critical : isDengue ? PALETTE.dengue : PALETTE.typhoid;
                    const glowColor = isCritical ? PALETTE.critical : isDengue ? PALETTE.dengueBright : PALETTE.typhoidBright;

                    return (
                      <g
                        key={r.id}
                        className={`map-node ${isSelected ? 'selected' : ''} ${isCritical ? 'critical-node' : ''} ${isDengue ? 'dengue-node' : 'typhoid-node'}`}
                        transform={`translate(${pt.x}, ${pt.y})`}
                        onClick={() => setSelectedId(r.id)}
                        onMouseEnter={e => handleMarkerHover(r, e)}
                        onMouseMove={e => handleMarkerHover(r, e)}
                        onMouseLeave={handleMarkerLeave}
                        style={{ cursor: 'pointer' }}
                      >
                        {/* Concentric Radar Wave */}
                        {(isCritical || viewMode === 'radar') && (
                          <circle
                            r={markerRadius * (isCritical ? 2.4 : 1.9)}
                            fill="none"
                            stroke={glowColor}
                            strokeWidth={isCritical ? "2.5" : "1.5"}
                            className={`radar-pulse-ring ${isCritical ? 'pulse-fast' : 'pulse-gentle'}`}
                            opacity={isCritical ? "0.85" : "0.55"}
                          />
                        )}

                        {/* Spotlight Reticle on Selection */}
                        {isSelected && (
                          <g className="spotlight-reticle" filter="url(#spotlight-glow)">
                            <circle r={markerRadius + 8} fill="none" stroke="#ffffff" strokeWidth="2.5" strokeDasharray="4 2" />
                            <line x1={-markerRadius - 12} y1="0" x2={-markerRadius - 4} y2="0" stroke="#ffffff" strokeWidth="2" />
                            <line x1={markerRadius + 4} y1="0" x2={markerRadius + 12} y2="0" stroke="#ffffff" strokeWidth="2" />
                            <line x1="0" y1={-markerRadius - 12} x2="0" y2={-markerRadius - 4} stroke="#ffffff" strokeWidth="2" />
                            <line x1="0" y1={markerRadius + 4} x2="0" y2={markerRadius + 12} stroke="#ffffff" strokeWidth="2" />
                          </g>
                        )}

                        {/* Solid Core Circle */}
                        <circle
                          r={markerRadius}
                          fill={isCritical ? "url(#grad-critical)" : isDengue ? "url(#grad-dengue)" : "url(#grad-typhoid)"}
                          stroke="#ffffff"
                          strokeWidth={isSelected ? "3" : "2"}
                          filter="url(#marker-shadow)"
                        />

                        {/* Center Icon */}
                        <text
                          y="4"
                          textAnchor="middle"
                          fontSize={markerRadius > 14 ? "12" : "10"}
                          fill="#ffffff"
                          fontWeight="bold"
                          style={{ pointerEvents: 'none' }}
                        >
                          {isDengue ? '🦟' : '🧫'}
                        </text>

                        {/* Label Badge */}
                        <g transform={`translate(${markerRadius + 6}, 4)`} className="node-label-group">
                          <rect
                            x="-2"
                            y="-11"
                            width={r.name.length * 7 + 38}
                            height="16"
                            rx="4"
                            fill="rgba(18, 44, 38, 0.88)"
                            stroke={isCritical ? "#e11d48" : isDengue ? "#2ec4b6" : "#f59e0b"}
                            strokeWidth="0.8"
                          />
                          <text x="3" y="1" className="node-city-text">{r.name}</text>
                          <text x={r.name.length * 7 + 10} y="1" className="node-case-tag">{r.projected_cases}</text>
                        </g>
                      </g>
                    );
                  })}
                </g>

                {/* Built-in Legend */}
                <g className="map-legend-layer" transform="translate(30, 560)">
                  <rect x="0" y="0" width="185" height="150" rx="8" fill="rgba(255,255,255,0.96)" stroke="#e2e8e4" />
                  <text x="14" y="22" fontWeight="700" fontSize="11" fill="#173a34">SURVEILLANCE LEGEND</text>
                  
                  <circle cx="22" cy="42" r="6" fill={PALETTE.dengue} stroke="#fff" strokeWidth="1.5" />
                  <text x="36" y="46" fontSize="10" fill="#334155" fontWeight="600">Dengue (Aedes vector)</text>

                  <circle cx="22" cy="64" r="6" fill={PALETTE.typhoid} stroke="#fff" strokeWidth="1.5" />
                  <text x="36" y="68" fontSize="10" fill="#334155" fontWeight="600">Typhoid (Salmonella H58)</text>

                  <circle cx="22" cy="86" r="6" fill={PALETTE.critical} stroke="#fff" strokeWidth="1.5" />
                  <circle cx="22" cy="86" r="10" fill="none" stroke={PALETTE.critical} strokeWidth="1" strokeDasharray="2 2" />
                  <text x="36" y="90" fontSize="10" fill="#e11d48" fontWeight="700">Critical Hotspot (Z ≥ 3.0)</text>

                  <circle cx="22" cy="110" r="5" fill={PALETTE.alert} />
                  <text x="36" y="114" fontSize="10" fill="#ea580c" fontWeight="600">Elevated Alert (Z ≥ 2.0)</text>

                  <circle cx="22" cy="130" r="4" fill={PALETTE.normal} />
                  <text x="36" y="134" fontSize="10" fill="#059669">Stable Baseline (Z &lt; 2.0)</text>
                </g>
              </svg>

              {/* Hover Tooltip */}
              {hoveredRegion && (
                <div
                  className="map-floating-tooltip"
                  style={{
                    left: `${tooltipPos.x + 14}px`,
                    top: `${tooltipPos.y - 12}px`
                  }}
                >
                  <div className="tooltip-head">
                    <strong>{hoveredRegion.name}</strong>
                    <span className={`tooltip-badge ${hoveredRegion.risk_level.toLowerCase()}`}>
                      {hoveredRegion.risk_level}
                    </span>
                  </div>
                  <div className="tooltip-body">
                    <div>Province: <span>{hoveredRegion.province}</span></div>
                    <div>Primary Disease: <b className={hoveredRegion.primary_disease.toLowerCase()}>{hoveredRegion.primary_disease}</b></div>
                    <div>Projected Volume: <b>{hoveredRegion.projected_cases} cases</b></div>
                    <div>Outbreak Z-Score: <b>Z {Number(hoveredRegion.z_score).toFixed(2)}</b></div>
                    <div className="tooltip-vector"><small>Vector: {hoveredRegion.dominant_vector}</small></div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Regional Epidemiological Dossier */}
        {(!isExpanded || drawerOpen) && (
          <div className={`card dossier-card ${isExpanded ? 'floating-dossier' : ''}`}>
            <div className="dossier-head">
              <div>
                <span className="dossier-tag">EPIDEMIOLOGICAL DOSSIER</span>
                <h2>{activeRegion.name} District</h2>
                <span className="dossier-province">{activeRegion.province} · {activeRegion.latitude.toFixed(2)}°N, {activeRegion.longitude.toFixed(2)}°E</span>
              </div>
              <div className={`dossier-risk-badge ${activeRegion.risk_level.toLowerCase()}`}>
                {activeRegion.risk_level} Risk
              </div>
            </div>

            {/* Disease Banner */}
            <div className={`dossier-disease-banner ${activeRegion.primary_disease.toLowerCase()}`}>
              <div className="banner-icon">
                {activeRegion.primary_disease === 'Dengue' ? '🦟' : '🧫'}
              </div>
              <div>
                <div className="banner-label">Primary Active Outbreak Disease</div>
                <h3>{activeRegion.primary_disease}</h3>
                <small>Secondary transmission: {activeRegion.secondary_disease || 'Monitored'}</small>
              </div>
              <div className="banner-status-chip">
                {activeRegion.status}
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="dossier-stats-grid">
              <div className="dossier-stat">
                <span className="stat-label">Projected Cases</span>
                <div className="stat-val">
                  {activeRegion.projected_cases}
                  <span className={`stat-trend ${activeRegion.case_change_pct > 0 ? 'up' : 'down'}`}>
                    {activeRegion.case_change_pct > 0 ? '▲' : '▼'} {Math.abs(activeRegion.case_change_pct)}%
                  </span>
                </div>
                <small>Monthly projection</small>
              </div>

              <div className="dossier-stat">
                <span className="stat-label">Outbreak Z-Score</span>
                <div className="stat-val text-zscore">
                  Z {Number(activeRegion.z_score).toFixed(2)}
                </div>
                <small>{activeRegion.z_score >= 3.0 ? 'Critical anomaly' : activeRegion.z_score >= 2.0 ? 'Alert threshold' : 'Within baseline'}</small>
              </div>

              <div className="dossier-stat">
                <span className="stat-label">Transmission Index</span>
                <div className="stat-val">
                  {activeRegion.transmission_index} / 100
                </div>
                <div className="transmission-progress-track">
                  <div
                    className={`transmission-progress-fill ${activeRegion.risk_level.toLowerCase()}`}
                    style={{ width: `${activeRegion.transmission_index}%` }}
                  ></div>
                </div>
              </div>

              <div className="dossier-stat">
                <span className="stat-label">Population at Risk</span>
                <div className="stat-val">
                  {activeRegion.population_at_risk_millions} Million
                </div>
                <small>Catchment zone</small>
              </div>
            </div>

            {/* Vector Clade */}
            <div className="dossier-section">
              <div className="section-title">
                <span>Dominant Transmission Vector & Clade</span>
              </div>
              <div className="vector-box">
                <div className="vector-icon">🧬</div>
                <div className="vector-info">
                  <strong>{activeRegion.dominant_vector}</strong>
                  <p>
                    {activeRegion.primary_disease === 'Dengue' 
                      ? 'Diurnal mosquito vector with daytime biting preference; breeding in stagnant domestic containers and rain reservoirs.'
                      : 'Bacterial transmission through contaminated water pipelines, sewage mixing, and food handler carriers.'}
                  </p>
                </div>
              </div>
            </div>

            {/* Sentinel Hospitals */}
            <div className="dossier-section">
              <div className="section-title">
                <span>Sentinel Hospital Network</span>
              </div>
              <div className="hospitals-chip-list">
                {(activeRegion.sentinel_hospitals || []).map((h, i) => (
                  <div key={i} className="hospital-chip">
                    <span className="hosp-glyph">🏥</span>
                    <div>
                      <strong>{h}</strong>
                      <small>Designated Triage & Isolation Ward</small>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Public Health Directive */}
            <div className="dossier-section directive-section">
              <div className="section-title text-directive">
                <span>Public Health Action Directive</span>
              </div>
              <div className="directive-quote-box">
                <div className="directive-marker">📋</div>
                <p>{activeRegion.public_health_directive}</p>
              </div>
            </div>

            {/* Clinical Screening CTA */}
            <div className="dossier-actions">
              <button
                className="btn primary dossier-cta-btn"
                onClick={() => onSelectForScreening && onSelectForScreening(activeRegion)}
              >
                ⊙ Run Patient Intake for {activeRegion.name} →
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Complete Affected Districts Matrix */}
      <article className="card panel map-table-panel">
        <div className="panel-head">
          <div>
            <h2>Comprehensive Affected Districts Matrix · Pakistan National Registry</h2>
            <p>Showing {filteredRegions.length} of {regions.length} districts · Click any row to focus that district on the map</p>
          </div>
          <div className="table-filter-stats">
            <span className="badge">Dengue: {filteredRegions.filter(r => r.primary_disease === 'Dengue').length}</span>
            <span className="badge typhoid">Typhoid: {filteredRegions.filter(r => r.primary_disease === 'Typhoid').length}</span>
            <span className="badge critical">Critical: {filteredRegions.filter(r => r.risk_level === 'Critical').length}</span>
          </div>
        </div>

        <div className="table-wrap">
          <table className="map-districts-table">
            <thead>
              <tr>
                <th>District / Area</th>
                <th>Province</th>
                <th>Primary Disease</th>
                <th>Secondary</th>
                <th>Risk Level</th>
                <th>Projected Cases</th>
                <th>MoM Trend</th>
                <th>Z-Score</th>
                <th>Transmission Index</th>
                <th>Dominant Vector</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredRegions.map(r => (
                <tr
                  key={r.id}
                  className={`table-row ${r.id === activeRegion?.id ? 'active-row' : ''}`}
                  onClick={() => setSelectedId(r.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <td>
                    <div className="table-city-cell">
                      <span className={`city-status-dot ${r.risk_level.toLowerCase()}`}></span>
                      <strong>{r.name}</strong>
                    </div>
                  </td>
                  <td>{r.province}</td>
                  <td>
                    <span className={`badge ${r.primary_disease.toLowerCase()}`}>
                      {r.primary_disease === 'Dengue' ? '🦟 Dengue' : '🧫 Typhoid'}
                    </span>
                  </td>
                  <td>{r.secondary_disease || 'None'}</td>
                  <td>
                    <span className={`badge ${r.risk_level.toLowerCase()}`}>
                      {r.risk_level}
                    </span>
                  </td>
                  <td>
                    <strong>{r.projected_cases.toLocaleString()}</strong>
                  </td>
                  <td>
                    <span className={`trend-cell ${r.case_change_pct > 0 ? 'up' : 'down'}`}>
                      {r.case_change_pct > 0 ? `+${r.case_change_pct}%` : `${r.case_change_pct}%`}
                    </span>
                  </td>
                  <td>
                    <span className="zscore-tag">Z {Number(r.z_score).toFixed(2)}</span>
                  </td>
                  <td>
                    <div className="table-progress-wrap">
                      <span>{r.transmission_index}</span>
                      <div className="mini-progress-bar">
                        <div
                          className={`mini-fill ${r.risk_level.toLowerCase()}`}
                          style={{ width: `${r.transmission_index}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="vector-cell" title={r.dominant_vector}>
                    <small>{r.dominant_vector}</small>
                  </td>
                  <td>
                    <button
                      className="btn small view-btn"
                      onClick={(e) => { e.stopPropagation(); setSelectedId(r.id); }}
                    >
                      Focus ⌖
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="footnote">
          National Infectious Disease Surveillance Registry · National University of Modern Languages (NUML) FYP.
        </div>
      </article>
    </div>
  );
}
