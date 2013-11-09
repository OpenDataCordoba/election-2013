"""
Quick utilities for cleaning up the source data.
"""
import csv
import json
import calculate
from pprint import pprint


class PalmeroFTW(object):
    """
    All the tricks.
    """
    primary_csv_path = "./input/votos_establecimiento_caba_paso.csv"
    general_csv_path = "./input/votos_establecimiento_cordoba_octubre.csv"
    location_json_path = "./input/locales_caba_paso2013.geojson"
#    location_json_path = "./input/escuelas.finales.972.json"
    location_json_path = "./input/DEMO_locales_cba_paso2013.geojson"

    listas = [
        '3',
        '47',
        '191',
        '217',
        '501',
        '503',
        '505',
        '512',
        '514',
        '9001',
        '9002',
        '9003',
        '9004',
        '9005',
        '9006',
    ]

    outheaders = [
        'fake_id',
#        '187', # Partido Autodeterminacion y Libertad (Dark blue)
#        '501', # Allanza Frente para la Victoria (Light Blue)
#        '502', # Allanza UNEN (Green)
#        '503', # Allanza Union Pro (Yellow)
#        '505', # Allanza Fet. de Izq.y de los Trabajadores (red)
#        '506', # Allanza Camino Popular (Gray)
        'overall_total',
    ] + listas

    outcsv_path = "output/merged_totals.csv"
    outjson_path = "output/merged_totals.geojson"

    def merge(self):
        """
        Merge the transformed csv file with the geojson with all
        the voting locations.
        """
        # Open raw geojson
        json_data = open(self.location_json_path, "rb").read()
        # Get it in Python
        json_data = json.loads(json_data)
        # Create list for stuff after we merge
        merged_features = []
        # Open the csv with results
        csv_data = csv.DictReader(open(self.outcsv_path, 'r'))
        # Key it by ID
        csv_data = dict((
            i['fake_id'], i
        ) for i in csv_data)
        # Loop through the features
        for row in json_data['features']:
            # Figure out each fake id
            fake_id = "%s-%s" % (
                row['properties']['mesa_desde'],
                row['properties']['mesa_hasta']
            )
            try:
                results_data = csv_data[fake_id]
            except KeyError:
                print "Does not have data for the tables %s" % fake_id
            # Filter it down to the data we want to keep
            merged_dict = {
                'geometry': row['geometry'],
#                'id': row['id'],
                'properties': {
                    'direccion': row['properties']['direccion'],
                    'establecim': row['properties']['establecim'],
                    'seccion': row['properties']['seccion'],
                    'circuito': row['properties']['circuito'],
                    'overall_total': int(results_data['overall_total']),
                    'fake_id': results_data['fake_id'],
                },
                'type': 'Feature'
            }
            merged_dict['properties']["votos"] = {}
            for party in self.listas:
                merged_dict['properties']["votos"][party] = int(results_data[party])

            # Toss it in the global list
            merged_features.append(merged_dict)
        # Structure out new merged JSON
        new_json = {
            'type': json_data['type'],
            'features': merged_features
        }
        # Write it out to a file
        outjson = open(self.outjson_path, "wb")
        outjson.write(json.dumps(new_json))

    def transform(self):
        """
        Transform the results file so that there is only one row
        for each precinct, with some summary stats calculated.
        """
        # Open the CSV
        general_csv = csv.DictReader(open(self.general_csv_path, 'r'))
        # Loop through the rows
        grouped_by_school = {}
        for row in general_csv:
            # And regroup them so each fake id is keyed to
            # all of the list totals for that precinct
            fake_id = "%s-%s" % (row['mesa_desde'], row['mesa_hasta'])
            try:
                grouped_by_school[fake_id][row['vot_parcodigo']] = row['total']
            except KeyError:
                grouped_by_school[fake_id] = {
                    row['vot_parcodigo']: row['total']
                }
        # Now loop through that
        outrows = []
        for fake_id, totals in grouped_by_school.items():
            # Figure out the overall total of votes
            overall_total = sum(map(int, totals.values()))
            # Start up a row to print out
            outrow = [fake_id,]
            # Load in the lists in the same "alphabetical" order
            for list_, total in sorted(totals.items(), key=lambda x:x[0]):
                outrow.append(int(total))
            # Load in the extra stuff we've calculated
            outrow.append(int(overall_total))
            # Add this row to the global list outside the loop
            outrows.append(outrow)
        # Open up a text file and write out all the data
        outcsv = csv.writer(open(self.outcsv_path, 'w'))
        outcsv.writerow(self.outheaders)
        outcsv.writerows(outrows)


if __name__ == '__main__':
    pftw = PalmeroFTW()
    pftw.transform()
    pftw.merge()
