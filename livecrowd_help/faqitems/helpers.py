from urllib.parse import parse_qs
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import urlunparse


def update_query_param(url, param, value):
    parsed_url = urlparse(url)
    # Parse the query parameters into a dictionary (with list values)
    query_params = parse_qs(parsed_url.query)
    # Update the parameter to the new value (as a list)
    query_params[param] = [str(value)]
    # Rebuild the query string
    new_query = urlencode(query_params, doseq=True)
    # Reconstruct the full URL with the updated query string
    return urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment,
        ),
    )
