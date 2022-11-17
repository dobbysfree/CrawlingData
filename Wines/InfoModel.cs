namespace WineCrawling
{
    public class InfoModel
    {
        public long code { get; set; }
        public string name { get; set; }

        public string winery { get; set; }
        public string wine_area { get; set; }
        public string variety { get; set; }
        public string type { get; set; }
        public string purpose { get; set; }
        public string alcohol { get; set; }
        public string temperature { get; set; }
        
        public int sweet { get; set; }
        public int acidity { get; set; }
        public int body { get; set; }
        public int tannin { get; set; }

        public string food { get; set; }
        public string price { get; set; }
        public string price_sub { get; set; }
        public string remark { get; set; }

        public string vintage_year { get; set; }
        public string vintage_note { get; set; }

        public string img_src { get; set; }
    }
}