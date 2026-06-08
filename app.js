const i18n = {
    zh: { title: "极简优质 RSS 导航", logo: "精选 RSS 导航", heading: "全球优质 RSS 源精选", sub: "聚合全球极具价值的订阅源，支持一键导入阅读器。", exportBtn: "📥 导出选中分类", langBtn: "English", copied: "已复制！", all: "全部 Feeds", tech: "💻 技术开发", blog: "💡 独立博客", news: "📰 资讯周刊", statusActive: "在线", statusDead: "待测", copyBtn: "复制链接" },
    en: { title: "Premium RSS Directory", logo: "Best RSS List", heading: "Curated Premium RSS Feeds", sub: "Global high-value subscription feeds, one-click export.", exportBtn: "📥 Export Selected OPML", langBtn: "简体中文", copied: "Copied!", all: "All Feeds", tech: "💻 Tech", blog: "💡 Blogs", news: "📰 News", statusActive: "Active", statusDead: "Pending", copyBtn: "Copy Link" }
};

let rssData = [];
let currentLang = 'zh';
let currentCategory = 'all';

function addNewSource() {
    const input = document.getElementById('new-url-input');
    let url = input.value.trim();
    if (!url) return alert("请输入有效的网址！");
    if (!url.startsWith("http")) url = "https://" + url;

    try {
        const domain = new URL(url).hostname;
        
        // 🟢 确保这里的用户名与您仓库完全一致
        const githubUser = "ai-root-no"; 
        const repoName = "NeW_RSS";
        
        const issueTitle = encodeURIComponent(`[ADD_RSS] ${domain}`);
        const issueBody = encodeURIComponent(`${url}`);
        
        // 🛠️ 修复核心：使用标准的模板字符串 `` 和 ${}，确保变量 100% 能够被正确替换
        const submitUrl = `https://github.com{githubUser}/${repoName}/issues/new?title=${issueTitle}&body=${issueBody}`;

        if(confirm("✨ 正在为您连接自动化数据库...\n\n点击确认后将跳转到 GitHub 页面。您只需直接点击绿色的 'Submit new issue' 按钮，机器人就会录入并刷新网站！")) {
            window.open(submitUrl, '_blank');
            input.value = "";
        }
    } catch (e) {
        alert("请输入合法的规范网址！");
    }
}


function toggleLanguage() { 
    currentLang = currentLang === 'zh' ? 'en' : 'zh'; 
    renderUI(); 
}

function renderUI() {
    const langData = i18n[currentLang];
    document.title = langData.title;
    document.getElementById('nav-logo').innerText = langData.logo;
    document.getElementById('main-heading').innerText = langData.heading;
    document.getElementById('main-sub').innerText = langData.sub;
    document.getElementById('btn-export').innerText = langData.exportBtn;
    document.getElementById('btn-lang').innerText = langData.langBtn;

    const categories = ['all', 'tech', 'blog', 'news'];
    document.getElementById('filter-container').innerHTML = categories.map(cat => `
        <button onclick="filterCategory('${cat}')" class="w-full text-left px-3 py-2 text-xs font-medium transition flex justify-between items-center border ${currentCategory === cat ? 'bg-slate-900 border-slate-900 text-white font-bold' : 'bg-slate-50 border-flatBorder text-slate-600 hover:bg-slate-100'}">
            <span>${langData[cat]}</span>
            ${currentCategory === cat ? '<span>✓</span>' : ''}
        </button>
    `).join('');

    const filteredData = currentCategory === 'all' ? rssData : rssData.filter(item => item.category === currentCategory);
    
    document.getElementById('rss-grid').innerHTML = filteredData.map(item => `
        <div class="bg-white border border-flatBorder p-4 flex flex-col justify-between hover:border-slate-400 transition group">
            <div>
                <div class="flex justify-between items-start gap-2">
                    <h3 class="font-bold text-slate-900 text-sm break-all leading-snug">${currentLang === 'zh' ? item.name : item.name_en}</h3>
                    <span class="text-[10px] font-bold px-1.5 py-0.5 tracking-wider uppercase shrink-0 ${item.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                        ${item.status === 'active' ? langData.statusActive : langData.statusDead}
                    </span>
                </div>
                <p class="text-[11px] text-slate-400 font-mono break-all mt-2 bg-slate-50 p-1.5 border border-slate-100 select-all">${item.url}</p>
            </div>
            <button onclick="copyToClipboard('${item.url}')" class="w-full mt-4 border border-slate-200 hover:border-blue-600 hover:bg-blue-600 hover:text-white text-slate-700 py-1.5 text-xs font-bold transition">
                ${langData.copyBtn}
            </button>
        </div>
    `).join('');
}

function filterCategory(cat) { currentCategory = cat; renderUI(); }
function copyToClipboard(text) { navigator.clipboard.writeText(text).then(() => alert(i18n[currentLang].copied)); }

function exportOPML() {
    const filteredData = currentCategory === 'all' ? rssData : rssData.filter(item => item.category === currentCategory);
    let opmlContent = `<?xml version="1.0" encoding="UTF-8"?>\n<opml version="1.0">\n  <head><title>Exported RSS Feeds</title></head>\n  <body>\n    <outline text="${currentCategory.toUpperCase()}" title="${currentCategory.toUpperCase()}">\n`;
    filteredData.forEach(item => {
        const name = currentLang === 'zh' ? item.name : item.name_en;
        opmlContent += `      <outline text="${name}" title="${name}" type="rss" xmlUrl="${item.url}" htmlUrl="${item.url}"/>\n`;
    });
    opmlContent += `    </outline>\n  </body>\n</opml>`;
    const blob = new Blob([opmlContent], { type: 'text/xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `rss_export_${currentCategory}.opml`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
}

async function init() {
    try {
        const response = await fetch('./data/sources.json');
        rssData = await response.json();
    } catch (error) {
        rssData = [
            { name: "知乎每日精选", name_en: "Zhihu", url: "https://zhihu.com", category: "news", status: "active" },
            { name: "阮一峰的网络日志", name_en: "RuanYiFeng", url: "https://ruanyifeng.com", category: "tech", status: "active" }
        ];
    }
    renderUI();
}
init();

