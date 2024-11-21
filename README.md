# SentinelHub CLI Tool

This Python-based command-line tool allows users to download Sentinel-2 imagery from SentinelHub based on an Area of Interest (AOI) file and a time range.

## Prerequisites

1. **Python 3.7+**  
   Ensure Python 3.7 or higher is installed. You can check your Python version with:
   ```bash
   python3 --version
   ```

### 2. **Required Python Packages**
Install the required dependencies using `pip`. It is recommended to use a virtual environment to isolate the project's dependencies.

#### Step-by-Step:

1. **Create a virtual environment**  
   Run the following command to create a virtual environment (named `venv`):

   ```bash
   python -m venv venv
   ```
2. **Activate the virtual environment**

After creating the virtual environment, activate it by running one of the following commands based on your operating system:

- For Linux/macOS:

  ```bash
  source venv/bin/activate
- For Windows:

  ```bash
  venv/Scripts/activate
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **SentinelHub Account**  
   You need a valid SentinelHub account and access to Sentinel-2 imagery. Obtain your **Client ID** and **Client Secret** from the [SentinelHub dashboard](https://www.sentinel-hub.com/).

## File Structure

```bash
├── cli_tool.py       # Main CLI tool script
├── requirements.txt  # List of dependencies
├── README.md         # Documentation
└── paris.geojson     # Sample AOI GeoJSON file
```

## Usage

Run the CLI tool with the following command:

```bash
python cli_tool.py --client_id <your-client-id> --client_secret <your-client-secret> --aoi_file <path-to-aoi-geojson> --toi "<start-date>/<end-date>" --image_type "<image-type>" --format "<image-format>"
```

### Parameters

- `--client_id`: Your **SentinelHub client ID**.
- `--client_secret`: Your **SentinelHub client secret**.
- `--aoi_file`: Path to the **AOI GeoJSON file** (polygon or multipolygon).
- `--toi`: **Time of Interest** in the format `YYYY-MM-DD/YYYY-MM-DD`.
- `--image_type`: Type of image to be processed:
    - `"visual"` for true-color RGB images.
    - `"ndvi"` for NDVI (vegetation index) images.
- `--format`: Format for the downloaded image (e.g., `tiff`, `png`).

### Example Command

```bash
python cli_tool.py --client_id xxxxx --client_secret xxxxx --aoi_file paris.geojson --toi "2023-01-01/2023-01-15" --image_type "ndvi" --format "tiff"
```

This will download Sentinel-2 NDVI imagery less than 20 percent cloud cover for the area defined in `paris.geojson` during the first 15 days of January 2023.

## Key Assumptions

- **AOI Validity**: The AOI file should be a valid GeoJSON file containing a polygon or multipolygon.
- **AOI Size**: The tool will ensure that the AOI bounding box does not exceed 100 km x 100 km. If it does, an error will be shown.
- **Cloud Cover**: The tool automatically filters images with cloud cover greater than 20%. This setting is fixed and cannot be changed.

## Code Overview

- **`create_sh_config(client_id, client_secret)`**: Creates a SentinelHub configuration using the provided credentials.
- **`read_aoi_file(aoi_file_path)`**: Reads the AOI file and checks its validity and size (ensures it is under 100 km x 100 km).
- **`generate_evalscript(image_type)`**: Generates an evaluation script based on the selected image type (`visual` or `ndvi`).
- **`download_image(image, aoi, config, image_type)`**: Handles the image download request from SentinelHub.

## Conclusion

This tool provides an easy way to download Sentinel-2 imagery for specific areas and time periods. Simply provide the required parameters, and the tool will handle the rest.
