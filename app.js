const i18n = {
    zh: { title: "极简优质 RSS 导航", logo: "精选 RSS 导航", heading: "全球优质 RSS 源精选", sub: "聚合全球极具价值的订阅源，支持一键导入阅读器。", exportBtn: "📥 导出 OPML 订阅包", langBtn: "English", copied: "已复制！", all: "全部 Feeds", tech: "💻 技术开发", blog: "💡 独立博客", news: "📰 资讯周刊", statusActive: "在线", statusDead: "超时", copyBtn: "复制链接", totalLbl: "总订阅源", activeLbl: "可用在线" },
    en: { title: "Premium RSS Directory", logo: "Best RSS List", heading: "Curated Premium RSS Feeds", sub: "Global high-value subscription feeds, one-click export.", exportBtn: "📥 Export Selected OPML", langBtn: "简体中文", copied: "Copied!", all: "All Feeds", tech: "💻 Tech", blog: "💡 Blogs", news: "📰 News", statusActive: "Active", statusDead: "Timeout", copyBtn: "Copy Link", totalLbl: "Total Feeds", activeLbl: "Active Feeds" }
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
        const githubUser = "ai-root-no"; 
        const repoName = "NeW_RSS";
        
        const issueTitle = encodeURIComponent(`[ADD_RSS] ${domain}`);
        const issueBody = encodeURIComponent(`${url}`);
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
    document.getElementById('lbl-total').innerText = langData.totalLbl;
    document.getElementById('lbl-active').innerText = langData.activeLbl;

    // 渲染实时大盘数据看板
    document.getElementById('stat-total').innerText = rssData.length;
    document.getElementById('stat-active').innerText = rssData.filter(item => item.status === 'active').length;

    // 渲染分类
    const categories = ['all', 'tech', 'blog', 'news'];
    document.getElementById('filter-container').innerHTML = categories.map(cat => {
        const count = cat === 'all' ? rssData.length : rssData.filter(i => i.category === cat).length;
        return `
            <button onclick="filterCategory('${cat}')" class="filter-item ${currentCategory === cat ? 'active' : ''}">
                <span>${langData[cat]}</span>
                <span style="opacity: 0.7; font-size: 11px;">(${count})</span>
            </button>
        `;
    }).join('');

    const filteredData = currentCategory === 'all' ? rssData : rssData.filter(item => item.category === currentCategory);
    
    // 渲染卡片
    document.getElementById('rss-grid').innerHTML = filteredData.map(item => `
        <div class="rss-card">
            <div class="card-header">
                <div class="card-title">${currentLang === 'zh' ? item.name : item.name_en}</div>
                <span class="status-badge ${item.status === 'active' ? 'active' : 'dead'}">
                    ${item.status === 'active' ? langData.statusActive : langData.statusDead}
                </span>
            </div>
            <div class="card-url">${item.url}</div>
            <button onclick="copyToClipboard('${item.url}')" class="card-btn">${langData.copyBtn}</button>
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
            { name: "阮一峰的网络日志", name_en: "RuanYiFeng", url: "https://ruanyifeng.com", category: "tech", status: "active" },
            { name: "少数派", name_en: "sspai", url: "https://sspai.com", category: "news", status: "active" }
        ];
    }
    renderUI();
}
init();
