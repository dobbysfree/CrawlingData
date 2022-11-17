using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using HtmlAgilityPack;
using MySql.Data.MySqlClient;

namespace WineCrawling
{
    class Program
    {
        static void Main(string[] args)
        {
            for (int idx = 164507; idx < 168608; idx++)
            {
                string url = "https://www.wine21.com/13_search/wine_view.html?Idx=" + idx;

                HtmlWeb web = new HtmlWeb();
                HtmlDocument doc = web.Load(url);

                InfoModel im = new InfoModel();

                var nodes = doc.DocumentNode.SelectSingleNode("//form[contains(@id, 'frmMain')]");
                if (nodes == null)
                    continue;

                im.code = idx;
                im.name = nodes.SelectSingleNode("//div[contains(@class, 'name_en')]").InnerText.Replace("'", "\\'");

                var src = nodes.SelectNodes("//div[contains(@class, 'column_detail1')]").ElementAt(0).ChildNodes.ElementAt(1);
                //int jpg = src.InnerHtml.IndexOf(".jpg");
                //int png = src.InnerHtml.IndexOf(".png");
                //int len = jpg == -1 ? png : jpg;

                im.img_src = src.InnerHtml.Substring(src.InnerHtml.IndexOf("http"), 63).Replace("'", "\\'");

                var winery = nodes.SelectNodes("//span[contains(@class, 'name_en')]");
                im.winery = winery.ElementAt(0).InnerText.Replace("'", "\\'");

                StringBuilder area = new StringBuilder();
                for (int i = 1; i < winery.Count; i++)
                {
                    var nm = winery.ElementAt(i).InnerText;

                    area.Append(nm);

                    if (i < winery.Count - 1)
                        area.Append(", ");
                }
                im.wine_area = area.ToString().Replace("'", "\'");

                var sub = nodes.SelectSingleNode("//div[contains(@class, 'wine_info')]").SelectNodes("//dd");                
                for (int i = 5; i < sub.Count; i++)
                {
                    string key = sub.ElementAt(i).PreviousSibling.PreviousSibling.InnerText.Replace(" ", "");
                    
                    if (key.Contains("품종")) im.variety = sub.ElementAt(i).InnerText.Trim().Replace("&nbsp;", "").Replace("\t", "").Replace("'", "\\'");
                    else if (key.Contains("종류")) im.type = sub.ElementAt(i).InnerText.Trim().Replace("&nbsp;", "");
                    else if (key.Contains("용도")) im.purpose = sub.ElementAt(i).InnerText.Trim().Replace("&nbsp;", "");
                    else if (key.Contains("알코올도수")) im.alcohol = sub.ElementAt(i).InnerText.Trim().Replace("&nbsp;", "");
                    else if (key.Contains("음용온도")) im.temperature = sub.ElementAt(i).InnerText.Trim().Replace("&nbsp;", "");
                    else if (key.Contains("당도")) im.sweet = int.Parse(sub.ElementAt(i).InnerHtml.Substring(sub.ElementAt(i).InnerHtml.IndexOf("SWEET") + 5, 1));
                    else if (key.Contains("산도")) im.acidity = int.Parse(sub.ElementAt(i).InnerHtml.Substring(sub.ElementAt(i).InnerHtml.IndexOf("ACIDITY") + 7, 1));
                    else if (key.Contains("바디")) im.body = int.Parse(sub.ElementAt(i).InnerHtml.Substring(sub.ElementAt(i).InnerHtml.IndexOf("BODY") + 4, 1));
                    else if (key.Contains("타닌")) im.tannin = int.Parse(sub.ElementAt(i).InnerHtml.Substring(sub.ElementAt(i).InnerHtml.IndexOf("TANNIN") + 6, 1));
                    else if (key.Contains("추천음식")) im.food = sub.ElementAt(i).InnerText.Trim().Replace("&nbsp;", "");
                    else if (key.Contains("가격"))
                    {
                        im.price = sub.ElementAt(i).ChildNodes.ElementAt(0).InnerText;
                        im.price_sub = sub.ElementAt(i).ChildNodes.ElementAt(2).InnerText.Replace("(", "").Replace(")", "");
                    }
                    else if (key.Contains("REMARK")) im.remark = sub.ElementAt(i).InnerText.Replace("\r\n", ", ").Replace("*", "").Replace("\"", "").Replace("'", "\\'");
                }

                var maker = nodes.SelectSingleNode("//div[contains(@class, 'vintage')]");
                if (maker != null)
                {
                    // 메이커노트
                    im.vintage_year = nodes.SelectSingleNode("//div[contains(@class, 'vintage')]").ChildNodes.ElementAt(1).InnerText;

                    if (!string.IsNullOrEmpty(im.vintage_year))
                    {
                        url = "https://www.wine21.com/13_search/load_wine_makernote.html?WineIdx=" + idx + "&VINTAGE=" + im.vintage_year;
                        web = new HtmlWeb();
                        doc = web.Load(url);

                        im.vintage_note = doc.DocumentNode.InnerText.Replace("\"", "").Replace("'", "\\'");
                    }
                }


                string query = string.Format("INSERT IGNORE INTO mst_wines VALUES ('{0}', '\"{1}\"', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}', '{10}', '{11}', '{12}', '{13}', '{14}', '{15}', '{16}', '{17}', '{18}', '{19}');",
                    im.code, im.name, im.winery, im.wine_area, im.variety, im.type, im.purpose, im.alcohol, im.temperature, im.sweet, im.acidity, im.body, im.tannin, im.food, im.price, im.price_sub, im.remark, im.vintage_year, im.vintage_note, im.img_src);

                Execute(idx.ToString(), query.Replace("\"", ""));

                Console.WriteLine("CURRENT > " + idx);

                Delay(1000);
            }

            Console.WriteLine("FINISH!");
        }

        #region Delay
        public static DateTime Delay(int MS)
        {
            DateTime ThisMoment = DateTime.Now;
            TimeSpan duration = new TimeSpan(0, 0, 0, 0, MS);
            DateTime AfterWards = ThisMoment.Add(duration);

            while (AfterWards >= ThisMoment)
            {
                ThisMoment = DateTime.Now;
            }
            return DateTime.Now;
        }
        #endregion

        #region execute
        static string sess = "Server=;Port=;Database=;UID=;PASSWORD=";
        public static int Execute(string code, string query)
        {
            int rst = 0;

            if (string.IsNullOrEmpty(query))
                return rst;

            using (MySqlConnection conn = new MySqlConnection(sess))
            {
                try
                {
                    conn.Open();
                    rst = new MySqlCommand(query, conn).ExecuteNonQuery();
                }
                catch (Exception)
                {
                    Console.WriteLine("DB ERROR > [" + code + "] " + query);
                    Write(query);
                    return -1;
                }
            }
            return rst;
        }
        #endregion

        static void Write(string msg)
        {
            using (StreamWriter sw = File.AppendText(@"G:\qrft\dev\Wines\Craw\bin\Debug\netcoreapp3.1\log.txt"))
            {
                sw.WriteLine(msg);
                sw.Close();
                sw.Dispose();
            }
        }
    }
}