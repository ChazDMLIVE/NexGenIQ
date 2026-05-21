/*
 * Example dataset for the Index Builder.
 *
 * Twenty illustrative Angus animals with EPDs for the core traits, used
 * by the "Run example data" button so a new user can see a real ranking
 * without preparing a file. These are made-up but realistic figures -
 * not real registered animals - and exist only to demonstrate the tool.
 * The same 20 animals are downloadable as a CSV from the animal step.
 */

import type { Animal } from "../lib/api";

export const EXAMPLE_ANGUS_ANIMALS: Animal[] = [
  {
    "animal_id": "AAA-20260137",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 42.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 129.0,
        "bif_accuracy": 0.8,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 1.96,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 12.0,
        "bif_accuracy": 0.75,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 6.0,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 36.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": -0.26,
        "bif_accuracy": 0.8,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": -0.08,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20260274",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 35.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 119.0,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 1.29,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 13.0,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 20.0,
        "bif_accuracy": 0.75,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 17.0,
        "bif_accuracy": 0.75,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.83,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.35,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20260411",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 48.0,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 100.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 1.82,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": -7.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 25.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 33.0,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.43,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.73,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20260548",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 92.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 96.0,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 1.0,
        "bif_accuracy": 0.8,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 15.0,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 23.0,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 16.0,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.32,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.13,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20260685",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 60.0,
        "bif_accuracy": 0.75,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 66.0,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": -0.22,
        "bif_accuracy": 0.75,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 2.0,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 8.0,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 33.0,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": -0.17,
        "bif_accuracy": 0.75,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.69,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20260822",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 63.0,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 122.0,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 6.41,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 5.0,
        "bif_accuracy": 0.8,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 16.0,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 26.0,
        "bif_accuracy": 0.8,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.55,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.31,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20260959",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 55.0,
        "bif_accuracy": 0.75,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 115.0,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": -1.53,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 9.0,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 16.0,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 21.0,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.42,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.25,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20261096",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 74.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 114.0,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 4.54,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 4.0,
        "bif_accuracy": 0.8,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 23.0,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 36.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.4,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.57,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20261233",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 99.0,
        "bif_accuracy": 0.75,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 109.0,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 2.87,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 1.0,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 16.0,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 8.0,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 1.01,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.59,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20261370",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 49.0,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 114.0,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 2.05,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 11.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 15.0,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 25.0,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.92,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.19,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20261507",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 70.0,
        "bif_accuracy": 0.8,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 132.0,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": -0.39,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 17.0,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 13.0,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 20.0,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.27,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.18,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20261644",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 63.0,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 89.0,
        "bif_accuracy": 0.8,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 0.78,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 9.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 28.0,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 24.0,
        "bif_accuracy": 0.75,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.54,
        "bif_accuracy": 0.75,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.63,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20261781",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 63.0,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 148.0,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 2.49,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 10.0,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 14.0,
        "bif_accuracy": 0.8,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 10.0,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.46,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.73,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20261918",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 45.0,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 97.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": -0.34,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 6.0,
        "bif_accuracy": 0.8,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 12.0,
        "bif_accuracy": 0.8,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 36.0,
        "bif_accuracy": 0.8,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 1.2,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.93,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20262055",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 40.0,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 73.0,
        "bif_accuracy": 0.8,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 2.57,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 15.0,
        "bif_accuracy": 0.75,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 20.0,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 22.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.19,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.79,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20262192",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 42.0,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 116.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 1.52,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 5.0,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 20.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 12.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.74,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.46,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20262329",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 81.0,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 94.0,
        "bif_accuracy": 0.8,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 3.85,
        "bif_accuracy": 0.75,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 5.0,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 15.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 49.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.1,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.28,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20262466",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 80.0,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 67.0,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 3.88,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 3.0,
        "bif_accuracy": 0.75,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 23.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 35.0,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.42,
        "bif_accuracy": 0.8,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.43,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20262603",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 78.0,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 50.0,
        "bif_accuracy": 0.75,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 0.54,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 13.0,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 24.0,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 34.0,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.78,
        "bif_accuracy": 0.75,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.4,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      }
    ]
  },
  {
    "animal_id": "AAA-20262740",
    "breed": "Angus",
    "evaluation_id": "AAA (American Angus Association)",
    "epds": [
      {
        "trait_code": "WW",
        "value": 64.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "YW",
        "value": 109.0,
        "bif_accuracy": 0.65,
        "scale": "EPD"
      },
      {
        "trait_code": "BW",
        "value": 1.28,
        "bif_accuracy": 0.85,
        "scale": "EPD"
      },
      {
        "trait_code": "CED",
        "value": 7.0,
        "bif_accuracy": 0.7,
        "scale": "EPD"
      },
      {
        "trait_code": "STAY",
        "value": 25.0,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "MILK",
        "value": 15.0,
        "bif_accuracy": 0.45,
        "scale": "EPD"
      },
      {
        "trait_code": "MARB",
        "value": 0.39,
        "bif_accuracy": 0.9,
        "scale": "EPD"
      },
      {
        "trait_code": "REA",
        "value": 0.23,
        "bif_accuracy": 0.55,
        "scale": "EPD"
      }
    ]
  }
];
