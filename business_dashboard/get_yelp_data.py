# This script scrapes yelp data by breaking up the region into small rectangles,
# and then aggregates the results. This is necessary because the Yelp API has a 40 response
# limit.

import cPickle as pickle
import sys

from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator

save_file_name = 'business_data_yelp_format.p'

def gather_data(start_lat, start_lng, end_lat, end_lng):
    print 'gathering yelp data for region:', start_lat, start_lng, end_lat, end_lng
    auth = Oauth1Authenticator(
        consumer_key='t_8t2Z_lEv5ViI1WsIvUBQ',
        consumer_secret='bcXs0gjWvOC5Pr2C_8FlTpe3t8s',
        token='x27Omv-oshm4iy-juSHCYi6m65sAcpWr',
        token_secret='_FnQse8dcibvnRe5kj-iBBecx7E'
    )

    client = Client(auth)

    params = {
        'limit': 40,
        'term': 'restaurants'
    }

    latlng_res = 0.01
    n_lat = int((end_lat - start_lat) / latlng_res)
    n_lng = int((end_lng - start_lng) / latlng_res)
    responses = []

    def do_one_box(start_lat, start_lng, end_lat, end_lng):
        res = client.search_by_bounding_box(start_lat, start_lng, end_lat, end_lng, **params)
        for i in res.businesses:
            name = i.name
            loc = i.location.coordinate
            if loc is not None:
                lat, lng = loc.latitude, loc.longitude
            else:
                lat, lng = 0, 0
            print name, lat, lng, i.eat24_url
        return res

    for i in range(n_lat):
        for j in range(n_lng):
            print 'box', i, j
            res = do_one_box(start_lat + i*latlng_res, start_lng + j*latlng_res,
                    start_lat + (i+1)*latlng_res, start_lng + (j+1)*latlng_res)
            responses.append(res)

    with open(save_file_name, 'wb') as f:
        pickle.dump(responses, f)

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print 'usage: python get_yelp_data.py start_lat start_lng end_lat end_lng'
        sys.exit()

    # Example regions:
    # MTV: 37.36 -122.16 37.43 -122.02
    gather_data(*(map(float, sys.argv[1:])))
    with open(save_file_name, 'rb') as f:
        responses = pickle.load(f)
        for res in responses:
            print len(res.businesses)
