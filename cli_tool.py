import os
import geopandas as gpd
import datetime
import click
from sentinelhub import SHConfig, SentinelHubCatalog, BBox, CRS, MimeType, SentinelHubRequest, DataCollection
from dotenv import load_dotenv
from utils import plot_ndvi_image

# Load environment variables from .env file
load_dotenv()

# Function to create SentinelHub configuration using CLI arguments
def create_sh_config(client_id, client_secret):
    config = SHConfig()

    # Set up your SentinelHub credentials from CLI arguments
    config.sh_client_id = client_id
    config.sh_client_secret = client_secret
    config.save()

    return config

# Function to read the AOI file (GeoJSON)
from shapely.geometry import box

# Function to read the AOI file and ensure the bounding box is no larger than 100km by 100km
def read_aoi_file(aoi_file_path):
    try:
        # Read the GeoJSON file using geopandas
        gdf = gpd.read_file(aoi_file_path)

        # Combine all geometries into a single bounding box using union_all
        unified_geom = gdf.geometry.union_all()  # Replaced unary_union with union_all
        if unified_geom.is_valid:
            bbox_coords = unified_geom.bounds  # Get the bounding box as (minx, miny, maxx, maxy)
            # Calculate the width and height of the bounding box in degrees
            minx, miny, maxx, maxy = bbox_coords
            width = maxx - minx
            height = maxy - miny
            # Convert degrees to kilometers (approximation, assuming WGS84 CRS)
            # 1 degree ~ 111.32 km
            width_km = width * 111.32
            height_km = height * 111.32

            # Check if the AOI exceeds the 100 km by 100 km limit
            if width_km > 100 or height_km > 100:
                print(f"Warning: AOI exceeds the 100 km x 100 km limit! ({width_km:.2f} km x {height_km:.2f} km)")

                # Optionally, split the AOI into smaller sections, or raise an error
                # For now, we can raise an error if the AOI is too large.
                print("Error: AOI is too large. Please ensure it's no larger than 100 km x 100 km.")
                return None  # or you can return None or handle it differently

            # Return the bounding box as a BBox object if it is valid and within size limits
            return BBox(bbox=bbox_coords, crs=CRS.WGS84)

        else:
            print("Error: AOI geometry is invalid.")
            return None
    except Exception as e:
        print(f"Error reading AOI file: {e}")
        return None



# Function to generate the evalscript dynamically
def generate_evalscript(image_type):
    if image_type == "visual":
        # RGB evalscript for true-color visualization
        return """
        //VERSION=3
        function setup() {
            return {
                input: ["B04", "B03", "B02"],
                output: { bands: 3 }
            };
        }

        function evaluatePixel(sample) {
            return [sample.B04, sample.B03, sample.B02];
        }
        """
    elif image_type == "ndvi":
        # NDVI evalscript for vegetation index
        return """
        //VERSION=3
        function setup() {
            return {
                input: ["B08", "B04"],
                output: { bands: 3 }
            };
        }

        function evaluatePixel(sample) {
            let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
            if (ndvi < -0.2) return [0.5, 0.5, 0.5];      // gray
            else if (ndvi < 0.0) return [0.8, 0.4, 0.0];  // brown
            else if (ndvi < 0.2) return [1.0, 1.0, 0.0];  // yellow
            else if (ndvi < 0.4) return [0.6, 0.8, 0.2];  // light green
            else if (ndvi < 0.6) return [0.2, 0.8, 0.2];  // green
            else return [0.0, 0.4, 0.0];                  // dark green
        }
        """
    else:
        raise ValueError("Invalid image type. Supported types are 'visual' and 'ndvi'.")

# Function to download image using SentinelHubRequest
def download_image_and_plot(image, aoi, config, image_type,image_format):

    image_time = image['properties'].get('datetime', None)
    if not image_time:
        print("Error: No valid date field found in image properties.")  # Helpful error message
        return None

    try:
        evalscript = generate_evalscript(image_type)
    except ValueError as e:
        print(f"Error: {e}")  # Error message for evalscript issues
        return None

    # Map the 'image_format' argument to the correct MimeType
    if image_format.lower() == 'png':
        mime_type = MimeType.PNG
    # elif image_format.lower() == 'tiff':
    #     mime_type = MimeType.TIFF
    else:
        print(f"Error: Unsupported format '{image_format}' requested.")
        return

    responses = [
        SentinelHubRequest.output_response(identifier="default", response_format=mime_type)
    ]


    data_folder = os.getcwd()

    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(image_time, image_time),
                maxcc=0.2,
                #size=(1024, 1024)
            )
        ],
        responses=responses,
        bbox=aoi,
        # size=(1024, 1024),
        config=config,
        data_folder=data_folder
    )

    try:
        print("Downloading image...")  # Inform the user about the download process
        response = request.get_data()
        print(f"Image downloaded and stored in variable")
        return response # Success message after download
    except Exception as e:
        print(f"Error downloading image: {e}")  # Error message for download failure
        return None


@click.command()
@click.option('--aoi_file', required=True, help="Path to the AOI file (GeoJSON format)")
@click.option('--toi', required=False, help="Time of interest in the format YYYY-MM-DD/YYYY-MM-DD")
@click.option('--image_type', required=True, type=click.Choice(['visual', 'ndvi'], case_sensitive=False), help="Type of the image to be processed: 'visual' or 'ndvi'")
@click.option('--image_format', required=True, help="Format of the image to be downloaded (e.g., tiff, png)")
@click.option('--client_id', required=False, help="Your SentinelHub client ID")
@click.option('--client_secret', required=False, help="Your SentinelHub client secret")
def main(aoi_file, toi, image_type, image_format, client_id, client_secret):
    # Si les identifiants ne sont pas fournis en ligne de commande, 
    # ils seront automatiquement pris depuis le fichier .env
    if not client_id:
        client_id = os.getenv('client_id')
    if not client_secret:
        client_secret = os.getenv('client_secret')

    # Read the AOI file and extract bounding box
    print(f"Reading AOI file from: {aoi_file}")  # Show the AOI file being processed
    aoi_bbox = read_aoi_file(aoi_file)
    if not aoi_bbox:
        print("Error: Could not read AOI file or invalid AOI.")  # Minimal error if AOI reading fails
        return

    # Set up the SentinelHub configuration with provided credentials
    print("Setting up SentinelHub configuration...")  # Show the setup is in progress
    config = create_sh_config(client_id, client_secret)

    if not toi:
        end_time = datetime.date.today()
        start_time = datetime.date.today() - datetime.timedelta(days=50)
        toi = f"{start_time.strftime('%Y-%m-%d')}/{end_time.strftime('%Y-%m-%d')}"
        print(f"Aucune période fournie, utilisation des 10 derniers jours : {toi}")


    # Set up the SentinelHubCatalog to search for images within the time range
    print(f"Searching for images between {toi}...")  # Inform about the image search
    catalog = SentinelHubCatalog(config=config)
    time_range = toi.split("/")
    start_time = datetime.datetime.strptime(time_range[0], "%Y-%m-%d")
    end_time = datetime.datetime.strptime(time_range[1], "%Y-%m-%d")

# Search for Sentinel-2 images within the time range and AOI
    images = catalog.search(
        bbox=aoi_bbox,
        time=(start_time, end_time),
        collection=DataCollection.SENTINEL2_L2A,
        filter="eo:cloud_cover<= 20",
        limit=50
    )

    if not images:
        print("No images found for the given AOI and time range.")  # Alert if no images found
        return

    # Convert the iterator to a list to access it by index
    image_list = list(images)

    # Check if there are any images and then process
    if image_list:
        image = image_list[0]  # Get the first image from the list

        # Try to access image properties safely
        try:
            print(f"Selected image from {image['properties']['datetime']}")  # Confirm which image was selected
        except KeyError:
            print("Error: The selected image does not contain a 'datetime' property.")  # Handle missing property

        # Download the selected image with specified type
        image_data = download_image_and_plot(image, aoi_bbox, config, image_type, image_format)
        if image_data:
            print(f"Image data downloaded successfully for {image['properties']['datetime']}.")
            # Ajouter la visualisation NDVI si le type d'image est 'ndvi'
            if image_type == 'ndvi':
                # Le tableau numpy est dans image_data[0]
                plot_ndvi_image(image_data[0])
        else:
            print("Error: Image data could not be downloaded.")
    else:
        print("No images found in the search results.")  # Handle case where no images are found in the list


if __name__ == "__main__":
    main()
