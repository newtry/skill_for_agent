#!/usr/bin/env python3
"""
巨潮资讯网年报下载器
从www.cninfo.com.cn下载脚本内已登记A股公司的年报、季报

功能：
1. 支持股票代码搜索
2. 支持单年或多年下载
3. 支持季报下载（Q1、半年报、Q3）
4. 自动过滤债券等非股票报告
"""

import os
import re
import time
import requests
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path


class CNINFODownloader:
    """
    巨潮资讯网年报下载器
    
    使用方法：
        downloader = CNINFODownloader("./annual_reports")
        files = downloader.download_annual_reports('600519', years=[2022, 2023, 2024])
    """
    
    SEARCH_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
    PDF_URL = "https://static.cninfo.com.cn/{}"
    
    STOCK_INFO = {
        '600519': {'name': '贵州茅台', 'orgId': 'gssh0600519'},
        '000001': {'name': '平安银行', 'orgId': 'gssz0000001'},
        '000002': {'name': '万科A', 'orgId': 'gssz0000002'},
        '000333': {'name': '美的集团', 'orgId': 'gssz0000333'},
        '000651': {'name': '格力电器', 'orgId': 'gssz0000651'},
        '000858': {'name': '五粮液', 'orgId': 'gssz0000858'},
        '002304': {'name': '洋河股份', 'orgId': 'gssz0002304'},
        '002415': {'name': '海康威视', 'orgId': 'gssz0002415'},
        '002594': {'name': '比亚迪', 'orgId': 'gssz0002594'},
        '300750': {'name': '宁德时代', 'orgId': 'gssz0030750'},
        '600036': {'name': '招商银行', 'orgId': 'gssh0600036'},
        '600276': {'name': '恒瑞医药', 'orgId': 'gssh0600276'},
        '600309': {'name': '万华化学', 'orgId': 'gssh0600309'},
        '600588': {'name': '用友网络', 'orgId': 'gssh0600588'},
        '600887': {'name': '伊利股份', 'orgId': 'gssh0600887'},
        '601318': {'name': '中国平安', 'orgId': 'gssh0601318'},
        '601398': {'name': '工商银行', 'orgId': 'gssh0601398'},
        '601888': {'name': '中国中免', 'orgId': 'gssh0601888'},
        '603259': {'name': '药明康德', 'orgId': 'gssh0603259'},
    }
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.cninfo.com.cn",
        "Referer": "https://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure"
    }
    
    def __init__(self, download_dir: str = "./annual_reports"):
        """
        初始化下载器
        
        Args:
            download_dir: 下载目录
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self._session = requests.Session()
        self._session.headers.update(self.HEADERS)
    
    def search_stock(self, keyword: str) -> Optional[Dict]:
        """
        搜索股票
        
        Args:
            keyword: 脚本内已登记的A股股票代码或名称，不支持拼音
            
        Returns:
            股票信息字典
        """
        normalized_keyword = re.sub(r"\s+", "", str(keyword))
        if normalized_keyword in self.STOCK_INFO:
            info = self.STOCK_INFO[normalized_keyword].copy()
            info['code'] = normalized_keyword
            return info
        
        for code, info in self.STOCK_INFO.items():
            if normalized_keyword == re.sub(r"\s+", "", info['name']):
                result = info.copy()
                result['code'] = code
                return result
        
        return None
    
    def _search_announcements_by_name(
        self,
        company_name: str,
        search_key: str,
        page_size: int = 30
    ) -> List[Dict]:
        """
        通过公司名称搜索公告
        
        Args:
            company_name: 公司名称
            search_key: 搜索关键词
            page_size: 每页数量
            
        Returns:
            公告列表
        """
        announcements = []
        page_num = 1
        max_pages = 10
        
        while page_num <= max_pages:
            try:
                data = {
                    'stock': '',
                    'tabName': 'fulltab',
                    'filedAnnouncementType': '',
                    'searchkey': f'{company_name} {search_key}',
                    'pageNum': str(page_num),
                    'pageSize': str(page_size),
                    'columnTitle': '历史公告查询',
                    'seDate': '',
                    'isHLtitle': 'true'
                }
                
                response = self._session.post(
                    self.SEARCH_URL,
                    data=data,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get('announcements') is None:
                    break
                
                announcements.extend(result['announcements'])
                
                total_count = result.get('totalAnnouncement', 0)
                if len(announcements) >= total_count or len(result['announcements']) < page_size:
                    break
                
                page_num += 1
                time.sleep(0.3)
                
            except Exception as e:
                print(f"搜索公告失败 (第{page_num}页): {e}")
                break
        
        return announcements
    
    def _download_pdf(self, url: str, filepath: Path) -> bool:
        """
        下载PDF文件
        
        Args:
            url: PDF URL
            filepath: 保存路径
            
        Returns:
            是否成功
        """
        try:
            response = self._session.get(
                self.PDF_URL.format(url),
                timeout=120,
                stream=True
            )
            
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            chunks = response.iter_content(chunk_size=8192)
            first_chunk = next(chunks, b"")
            if not first_chunk.startswith(b"%PDF") and "pdf" not in content_type:
                print("下载内容不是PDF，已放弃保存")
                return False

            temporary_path = filepath.with_suffix(filepath.suffix + ".part")
            with open(temporary_path, 'wb') as f:
                f.write(first_chunk)
                for chunk in chunks:
                    if chunk:
                        f.write(chunk)
            os.replace(temporary_path, filepath)
            return True
                
        except Exception as e:
            print(f"下载PDF失败: {e}")
            return False
    
    def download_annual_reports(
        self,
        stock_keyword: str,
        year: int = None,
        years: List[int] = None,
        include_summary: bool = False,
        output_dir: str = None
    ) -> List[str]:
        """
        下载年度报告
        
        Args:
            stock_keyword: 股票代码或名称
            year: 单年
            years: 多年列表
            include_summary: 是否包含摘要报告
            output_dir: 输出目录
            
        Returns:
            下载的文件路径列表
        """
        stock_info = self.search_stock(stock_keyword)
        if stock_info is None:
            print(f"未找到股票: {stock_keyword}")
            print(f"支持的股票代码: {', '.join(list(self.STOCK_INFO.keys())[:10])}...")
            return []
        
        code = stock_info.get('code', stock_keyword)
        name = stock_info.get('name', stock_keyword)
        
        print(f"找到股票: {code} - {name}")
        
        if years is None:
            if year is None:
                years = [datetime.now().year - 1]
            else:
                years = [year]
        
        output_path = Path(output_dir) if output_dir else self.download_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        downloaded_files = []
        
        print(f"正在搜索年度报告...")
        announcements = self._search_announcements_by_name(name, '年度报告')
        print(f"找到 {len(announcements)} 条公告")
        
        for target_year in years:
            year_str = str(target_year)
            year_patterns = [
                f"{year_str}年年度报告",
                f"{year_str}年度报告",
            ]
            
            matched_announcements = []
            for ann in announcements:
                title = ann.get('announcementTitle', '')
                title_clean = re.sub(r'<[^>]+>', '', title)
                sec_code = ann.get('secCode', '')
                
                if sec_code != code:
                    continue
                
                for pattern in year_patterns:
                    if pattern in title_clean:
                        if '摘要' in title_clean and not include_summary:
                            continue
                        if '半年度' in title_clean:
                            continue
                        if '英文' in title_clean:
                            continue
                        matched_announcements.append(ann)
                        break
            
            if not matched_announcements:
                print(f"未找到 {target_year} 年度报告")
                continue
            
            for ann in matched_announcements:
                title = ann.get('announcementTitle', '')
                title_clean = re.sub(r'<[^>]+>', '', title)
                url = ann.get('adjunctUrl', '')
                
                if not url:
                    continue
                
                suffix = '摘要' if '摘要' in title_clean else ''
                filename = f"{code}_{name}_{target_year}年年度报告{suffix}.pdf"
                filepath = output_path / filename
                
                if filepath.exists():
                    print(f"文件已存在: {filename}")
                    downloaded_files.append(str(filepath))
                    continue
                
                print(f"正在下载: {filename}")
                if self._download_pdf(url, filepath):
                    print(f"下载成功: {filename}")
                    downloaded_files.append(str(filepath))
                else:
                    print(f"下载失败: {filename}")
                
                time.sleep(1)
        
        return downloaded_files
    
    def download_quarterly_reports(
        self,
        stock_keyword: str,
        year: int = None,
        output_dir: str = None
    ) -> List[str]:
        """
        下载季度报告
        
        Args:
            stock_keyword: 股票代码或名称
            year: 年份（默认最新年份）
            output_dir: 输出目录
            
        Returns:
            下载的文件路径列表
        """
        stock_info = self.search_stock(stock_keyword)
        if stock_info is None:
            print(f"未找到股票: {stock_keyword}")
            return []
        
        code = stock_info.get('code', stock_keyword)
        name = stock_info.get('name', stock_keyword)
        
        print(f"找到股票: {code} - {name}")
        
        if year is None:
            year = datetime.now().year
        
        output_path = Path(output_dir) if output_dir else self.download_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        downloaded_files = []
        
        print(f"正在搜索季度报告...")
        announcements = self._search_announcements_by_name(name, '季度报告')
        print(f"找到 {len(announcements)} 条公告")
        
        quarterly_patterns = [
            (f'{year}年第一季度报告', f'{year}年第一季度报告.pdf'),
            (f'{year}年一季度报告', f'{year}年第一季度报告.pdf'),
            (f'{year}年半年度报告', f'{year}年半年度报告.pdf'),
            (f'{year}年第三季度报告', f'{year}年第三季度报告.pdf'),
            (f'{year}年三季度报告', f'{year}年第三季度报告.pdf'),
        ]
        
        for search_pattern, filename_suffix in quarterly_patterns:
            matched_announcements = []
            
            for ann in announcements:
                title = ann.get('announcementTitle', '')
                title_clean = re.sub(r'<[^>]+>', '', title)
                sec_code = ann.get('secCode', '')
                url = ann.get('adjunctUrl', '')
                
                if sec_code != code:
                    continue
                
                if search_pattern in title_clean:
                    matched_announcements.append({
                        'title': title_clean,
                        'url': url,
                        'sec_code': sec_code
                    })
            
            if not matched_announcements:
                print(f"未找到: {search_pattern}")
                continue
            
            for ann in matched_announcements:
                filename = f"{ann['sec_code']}_{name}_{filename_suffix}"
                filepath = output_path / filename
                
                if filepath.exists():
                    print(f"文件已存在: {filename}")
                    downloaded_files.append(str(filepath))
                    continue
                
                print(f"正在下载: {filename}")
                if self._download_pdf(ann['url'], filepath):
                    print(f"下载成功: {filename}")
                    downloaded_files.append(str(filepath))
                else:
                    print(f"下载失败: {filename}")
                
                time.sleep(1)
        
        return downloaded_files


def main():
    """
    命令行入口
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='巨潮资讯网年报下载器')
    parser.add_argument('stock', help='股票代码或名称')
    parser.add_argument('--year', type=int, help='下载指定年份')
    parser.add_argument('--years', type=str, help='下载多个年份，逗号分隔')
    parser.add_argument('--output-dir', '-o', type=str, default='./annual_reports', help='输出目录')
    parser.add_argument('--include-summary', action='store_true', help='包含摘要报告')
    parser.add_argument('--quarterly', action='store_true', help='下载季报')
    
    args = parser.parse_args()
    
    downloader = CNINFODownloader(args.output_dir)
    
    if args.years:
        years = [int(y.strip()) for y in args.years.split(',')]
    else:
        years = None
    
    if args.quarterly:
        files = downloader.download_quarterly_reports(
            args.stock,
            year=args.year,
            output_dir=args.output_dir
        )
    else:
        files = downloader.download_annual_reports(
            args.stock,
            year=args.year,
            years=years,
            include_summary=args.include_summary,
            output_dir=args.output_dir
        )
    
    print(f"\n下载完成，共 {len(files)} 个文件")
    for f in files:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
