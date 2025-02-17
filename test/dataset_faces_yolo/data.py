import yaml

data = {
    'path': '/home/elisa/uni/tfg-ematos/test/dataset_faces_yolo',  
    'train': 'images/train',  
    'val': 'images/val',  
    'names': {
        0: 'Elisa',
        1: 'Adri'
    }
}

with open('../dataset_faces_yolo/data.yaml', 'w') as file:
    yaml.dump(data, file, 
              default_flow_style=False, 
              sort_keys=False)
