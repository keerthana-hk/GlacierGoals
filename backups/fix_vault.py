with open(r'd:\2026 resolution tracker\templates\vault.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the duplicated closing divs introduced by the bad replacement
bad = '    </div>         </div>\r\n        </div>\r\n    </div>\r\n\r\n    <!-- Flipbook'
good = '    </div>\r\n\r\n    <!-- Flipbook'
if bad in content:
    content = content.replace(bad, good)
    print('Fixed duplicate divs')
else:
    # Try without carriage returns
    bad2 = '    </div>         </div>\n        </div>\n    </div>\n\n    <!-- Flipbook'
    good2 = '    </div>\n\n    <!-- Flipbook'
    if bad2 in content:
        content = content.replace(bad2, good2)
        print('Fixed duplicate divs (LF version)')
    else:
        print('Pattern not found - checking nearby text')
        idx = content.find('Flipbook Cinema')
        print(repr(content[idx-200:idx]))

with open(r'd:\2026 resolution tracker\templates\vault.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
