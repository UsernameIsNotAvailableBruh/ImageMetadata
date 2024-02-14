import PIL.Image, PIL.ExifTags
import os.path, pathlib
import json
import fractions

class ImageMetaData:
    def _GetDir(self, Path = pathlib.Path(f"{''.join(__file__.split(".")[:-1])}.json")):
        return json.load(
            open(Path, "r")
        )

    def _StoreDir(self, Dir, Path = pathlib.Path(f"{''.join(__file__.split(".")[:-1])}.json")):
        if os.path.isdir(Dir):
            json.dump(
                {"SearchDir": Dir},
                open(Path, "w")
            )

    def DirDecider(self):
        SearchDir = os.getcwd()
        Input = input(f"\nIn which directory should images be searched for?\n(1) Use {SearchDir} or (2) Another Directory\n")
        if not Input in ("1", "2"):
            self.DirDecider()
        if Input == "2":
            DirInput = os.path.dirname(input("Directory:\n")+str(pathlib.Path("/")))
            while not os.path.isdir(DirInput):
                print(f"Could not find {DirInput}")
                print("Enter directory or a folder")
                DirInput = os.path.dirname(input("Directory:\n")+str(pathlib.Path("/")))
            SearchDir = DirInput
        self._StoreDir(SearchDir)
        return SearchDir

    def Searcher(self, Search: str, SearchDir: str | pathlib.Path, ExcludeSearch: list = "", IncludeFolders: bool = False, IncludeFiles: bool = True, Abs: bool= True):
        print(f"Searching in {SearchDir}")
        #.py .pdf .bash .sldprt .stl .txt .rpm .json
        FileFound = []
        FoldersFound = []
        DirList = os.listdir(SearchDir)
        print(f"there are {len(DirList)} files and/or folders in {SearchDir}")
        for x in DirList:
            ContainsSearch = (Search.lower() in x.lower())
            if ExcludeSearch == [""]:
                NotContainExcludeSearch = True #doesnt have a exclude search
            else:
                NotContainExcludeSearch = all([x.lower().find(y)==-1 for y in ExcludeSearch ])
            #print(ContainsSearch, NotContainExcludeSearch, x)
            if Abs and not os.path.isabs(x): 
                x = str(pathlib.Path(f"{SearchDir}/{x}")) #make x a absolute path 
            if NotContainExcludeSearch and ContainsSearch:
                if os.path.isfile(x): #Means x is a file
                    FileFound.append(x)
                elif os.path.isdir(x): #Means x is a folder/directory
                    FoldersFound.append(x)
        if IncludeFolders and IncludeFiles:
            return FoldersFound, FileFound
        elif IncludeFiles:
            return FileFound
        elif IncludeFolders:
            return FoldersFound
        return []
    
    def main(self, Abs=True, indent=4):
        if not os.path.exists(pathlib.Path(f"{''.join(__file__.split(".")[:-1])}.json")): #run if doesn't exist
            SearchDir = self.DirDecider()
        else:
            SearchDir = self._GetDir()["SearchDir"]
            if input(f"Use last used directory? ({SearchDir})\n(1 for yes, 0 for no)\n") == "0":
                SearchDir = self.DirDecider()

        Search = input("Search for images containing:\n")
        Files = self.Searcher(Search, SearchDir, ExcludeSearch=input("What should be excluded in your search?\n(If multiple, separate by space)\n").split(" "), Abs=Abs)

        print(f"{(Before := len(Files))} files found.")

        for x in Files:
            try:
                PIL.Image.open(x)
            except PIL.UnidentifiedImageError as e:
                Files.remove(x)

        print(f"Out of {Before}, {len(Files)} images found. ({len(Files)/Before:.02%} were images)")

        ListDict:list[tuple[str, dict]] = []
        for x in Files:
            #https://exiv2.org/tags.html is really helpful for this part and google searches
            Image = PIL.Image.open(x)
            EXIF = Image.getexif()
            IFD = EXIF.get_ifd(34665)
            ListDict.append((x, dict()))
            Dict = ListDict[-1][1]
            for x, y in IFD.items():
                if x == 37500: continue #skip makernote
                try:
                    Dict |= {PIL.ExifTags.Base(x).name: y}
                except:
                    if x == 37396: #Pillow doesn't have this one
                        Dict |= {"SubjectArea":y}
                    else:
                        print(f"Unknown exif tag: {x} (will be ignored)")
                    Dict |= {x:y}

        Order = ["FocalLength", "ExposureTime", "ISOSpeedRatings", "FNumber"]
        OrderPostUnit = ["mm", "s", "", ""]
        OrderPreUnit = ["", "", "ISO ", "f/"]
        OutputDict = dict()
        for ImagePath, Dict in ListDict:
            ImageDict = dict()
            for Setting, PreUnit, PostUnit in zip(Order, OrderPreUnit, OrderPostUnit):
                if Setting == "ExposureTime":
                    if Dict.get(Setting, "N/A") == "N/A":
                        ImageDict |= {Setting: f"Unknown Exposure Time"}
                        continue
                    Dict[Setting] = str(fractions.Fraction(Dict[Setting]).limit_denominator())
                ImageDict |= {Setting: f"{PreUnit}{Dict.get(Setting, " Unknown ")}{PostUnit}"}
            OutputDict |= {ImagePath: ImageDict}
        Current = dict()
        try:
            open(pathlib.Path(f"{os.path.dirname(__file__)}/ImageStoredMetaData.json"), "x") #makes new file, raises error if file exists
        except:
            Current = json.load(open(pathlib.Path(f"{os.path.dirname(__file__)}/ImageStoredMetaData.json"), "r"))
        Current.update({SearchDir : OutputDict})
        json.dump(Current, fp=open(pathlib.Path(f"{os.path.dirname(__file__)}/ImageStoredMetaData.json"), "w"), indent=indent)

if __name__ == "__main__":
    ImageMetaData().main()