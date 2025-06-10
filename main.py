#this program will check all ID against api to see if in-store exists
#maybe log it? Idk

from legacyTarget import get_target_product_data
import configparser
import os
import sys

base_path = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
tcin_path = os.path.join(base_path, "tcin.ini")

config = configparser.ConfigParser()
config.read(tcin_path)

def main():
    # print(f"Loading tcin from: {tcin_path}")
    print("TCIN test:")
    #tcin = str(input())
    #tcins = ["77464001", "12953464", "12953461"]
    #tcins = ["77464001"] #nintendo switch
    tcins = ["93954435"] #ETB Prismatic Evolutions
    print("Using zipcode 98042")
    zip_code = "98042"
    tcin = "77464001"
    store_id = "681"
    get_target_product_data(tcin, store_id)

    
    



if __name__ == "__main__":
    main()