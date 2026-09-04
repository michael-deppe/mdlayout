local json = require 'pandoc.json'
local data_file = os.getenv('MDLAYOUT_HTML_DATA') or 'mdlayout-html-data.json'
local fh = assert(io.open(data_file, 'r'))
local data = json.decode(fh:read('*a')); fh:close()

local classes = {
  FullArea='fullarea', HalfArea='halfarea', DirectoryArea='directoryarea',
  MarginArea='marginarea', marginarea='marginarea', note='note', warning='warning',
  SynchronizedMarginAndTextArea='synchronized', TextInMarginArea='marginarea-content',
  TextInTextArea='textarea-content', typewriter='typewriter', MarginFigure='marginfigure',
  widefigure='widefigure', widetable='widetable', FullCenter='fullcenter',
  Center='center', titlepage='titlepage', footnotesize='tex-size-footnotesize'
}

local function make_image(spec)
  local attrs = {}
  if spec.width then attrs[#attrs+1] = {'style', 'width:'..spec.width..';max-width:100%;height:auto'} end
  return pandoc.Image({pandoc.Str('image')}, spec.source, '',
    pandoc.Attr('', {'latex-image'}, attrs))
end

local function listing_block(index)
  local function esc(s)
    return (s:gsub('&','&amp;'):gsub('<','&lt;'):gsub('>','&gt;'):gsub('"','&quot;'))
  end
  local label = ((data.listings or {})[tostring(index)] or 'Listing')
  local code = data.codeblocks[index+1] or ''
  local lines = {}
  for line in (code..'\n'):gmatch('(.-)\n') do
    lines[#lines+1] = '<span class="listing-line">'..esc(line)..'</span>'
  end
  return pandoc.RawBlock('html',
    '<figure class="latex-listing fullarea">\n<figcaption>'..esc(label)
    ..'</figcaption>\n<pre><code>'..table.concat(lines, '')
    ..'</code></pre>\n</figure>')
end

local function printout_block(index)
  local function esc(s)
    return (s:gsub('&','&amp;'):gsub('<','&lt;'):gsub('>','&gt;'):gsub('"','&quot;'))
  end
  local spec = (data.printouts or {})[tostring(index)] or {}
  local code = data.codeblocks[index+1] or ''
  local bandlines = tonumber(spec.bandlines) or 0
  local feedlines = tonumber(spec.feedlines) or 0
  local paperheight = math.min(999, math.max(1, tonumber(spec.paperheight) or 999))
  local color = spec.color or 'none'
  local classes = {'printout', 'fullarea', 'printout-'..color}
  local fontsize = (spec.fontsize or '\\normalsize'):gsub('^\\', ''):gsub('[^%w_-]', '')
  classes[#classes+1] = 'printout-size-'..fontsize
  if spec.linenumbers == 'true' then classes[#classes+1] = 'has-line-numbers' end
  if spec.punchholes == 'true' then classes[#classes+1] = 'has-punchholes' end
  local lines, number = {}, 0
  for line in (code..'\n'):gmatch('(.-)\n') do
    number = number + 1
    local paperline = ((number-1) % paperheight)+1
    local lineclasses = {'printout-line'}
    if bandlines > 0 then
      lineclasses[#lineclasses+1] = (math.floor((paperline-1)/bandlines) % 2 == 0)
        and 'band-light' or 'band-dark'
      if (paperline-1) % bandlines == 0 then lineclasses[#lineclasses+1] = 'band-start' end
    end
    if feedlines > 0 and (paperline-1) % feedlines == 0 then
      lineclasses[#lineclasses+1] = 'feed-hole'
    end
    if paperline == 1 then lineclasses[#lineclasses+1] = 'paper-start' end
    if paperline == paperheight then lineclasses[#lineclasses+1] = 'paper-end' end
    local n = tostring(paperline)
    lines[#lines+1] = '<span class="'..table.concat(lineclasses, ' ')..'">'
      ..'<span class="printout-number printout-number-left">'..n..'</span>'
      ..'<span class="printout-text">'..esc(line)..'</span>'
      ..'<span class="printout-number printout-number-right">'..n..'</span></span>'
  end
  local style = '--fit-columns:'..esc(spec.fitcolumns or '132')
    ..';--paper-height:'..esc(spec.paperheight or '999')
    ..';--band-lines:'..esc(spec.bandlines or '0')
    ..';--feed-lines:'..esc(spec.feedlines or '0')
  return pandoc.RawBlock('html', '<figure class="'..table.concat(classes, ' ')
    ..'" style="'..style..'"><pre><code>'..table.concat(lines, '')
    ..'</code></pre></figure>')
end

local function see_right(scale)
  local primary = (data.colors or {}).mdColorPrimary or 'rgb(3,28,93)'
  return pandoc.RawInline('html', '<span class="md-see-right" role="img" '
    ..'aria-label="See right" style="font-size:'..scale
    ..'em;background-color:'..primary..'"></span>')
end

local function make_wordmark()
  local primary = (data.colors or {}).mdColorPrimary or 'rgb(3,28,93)'
  local md = pandoc.Span({pandoc.Str('md')},
    pandoc.Attr('', {'mdlayout-md'}, {{'style', 'color: '..primary}}))
  return pandoc.Span({md, pandoc.Str('layout')},
    pandoc.Attr('', {'mdlayout-wordmark'}, {}))
end

local function latex_blocks(s)
  s = s:gsub('\\MDSeeRight{([0-9.]+)}', function(scale)
    return ' MDSEERIGHTSCALE'..scale:gsub('%.', 'p')..'END '
  end)
  local doc = pandoc.read(s, 'latex+raw_tex')
  doc = doc:walk({Str = function(el)
    local scale = el.text:match('^MDSEERIGHTSCALE([0-9p]+)END$')
    if scale then return see_right(scale:gsub('p', '.')) end
  end, RawInline = function(el)
    local n = el.text:match('^\\MDImage{(%d+)}$')
    if n then return make_image(data.images[tonumber(n)+1]) end
  end, RawBlock = function(el)
    local n = el.text:match('^%s*\\MDImage{(%d+)}%s*$')
    if n then return pandoc.Para({make_image(data.images[tonumber(n)+1])}) end
    n = el.text:match('^%s*\\MDTextAreaCodeBlock{(%d+)}%s*$')
    if n then
      return pandoc.Div(
        {pandoc.CodeBlock(data.codeblocks[tonumber(n)+1] or '')},
        pandoc.Attr('', {'textarea-content', 'verbatim-in-textarea'}, {}))
    end
  end})
  return doc.blocks
end

local function latex_inlines(s)
  local d = pandoc.read(s, 'latex+raw_tex')
  d = d:walk({RawInline = function(el)
    if el.text:match('^\\MDWordmark%s*$') then
      return {make_wordmark(), pandoc.Space()}
    end
    local n = el.text:match('^\\MDCodeInline{(%d+)}$')
    if n then return pandoc.Code(data.codeinlines[tonumber(n)+1] or '') end
    n = el.text:match('^\\MDLatexInline{(%d+)}$')
    if n then
      return pandoc.Code(data.codeinlines[tonumber(n)+1] or '',
        pandoc.Attr('', {'latex-fragment'}, {}))
    end
  end})
  if #d.blocks == 1 and d.blocks[1].content then return d.blocks[1].content end
  return {pandoc.Str(pandoc.utils.stringify(d))}
end

local function clean_table_row(row)
  local cleaned, spacing = {}, nil
  for i,raw in ipairs(row) do
    raw = raw:gsub('\\addlinespace%s*%[([^%]]+)%]', function(amount)
      if not spacing and amount:match('^[%d.]+[A-Za-z%%]+$') then spacing = amount end
      return ''
    end)
    raw = raw:gsub('\\addlinespace', function()
      if not spacing then spacing = '.5em' end
      return ''
    end)
    cleaned[i] = raw:gsub('^%s+', '')
  end
  return cleaned, spacing
end

local function make_table(spec)
  local function esc(s)
    return (s:gsub('&','&amp;'):gsub('<','&lt;'):gsub('>','&gt;'):gsub('"','&quot;'))
  end
  local function render(raw, col, is_header)
    if not is_header then
      for _,n in ipairs(spec.verbatim_columns or {}) do
        if n == col then return '<code>'..esc(raw)..'</code>' end
      end
    end
    local html = pandoc.write(pandoc.Pandoc({pandoc.Plain(latex_inlines(raw))}), 'html')
    html = html:gsub('^%s*<p>',''):gsub('</p>%s*$',''):gsub('%s+$','')
    if not is_header then
      for _,n in ipairs(spec.typewriter_columns or {}) do
        if n == col then return '<span class="typewriter-cell">'..html..'</span>' end
      end
    end
    return html
  end
  local function alignment_attr(col)
    for _,n in ipairs(spec.center_columns or {}) do
      if n == col then return ' class="align-center"' end
    end
    for _,n in ipairs(spec.right_columns or {}) do
      if n == col then return ' class="align-right"' end
    end
    for _,n in ipairs(spec.left_columns or {}) do
      if n == col then return ' class="align-left"' end
    end
    return ''
  end
  local id = spec.options and spec.options.label or nil
  local idattr = id and (' id="'..esc(id)..'"') or ''
  local out={'<table class="reference-table"'..idattr..'>'}
  if spec.options and spec.options.caption then
    local prefix = spec.number and ('<span class="table-number">Table '..string.format('%g', spec.number)..': </span>') or ''
    out[#out+1]='<caption>'..prefix..render(spec.options.caption, 0)..'</caption>'
  end
  if spec.headers and #spec.headers > 0 then
    out[#out+1]='<thead><tr>'
    for i=1,spec.columns do out[#out+1]='<th scope="col"'..alignment_attr(i)..'>'..render(spec.headers[i] or '', i, true)..'</th>' end
    out[#out+1]='</tr></thead>'
  end
  out[#out+1]='<tbody>'
  for _,row in ipairs(spec.rows or {}) do
    local cells, spacing = clean_table_row(row)
    local style = spacing and (' class="add-line-space" style="--md-row-space:'..spacing..'"') or ''
    out[#out+1]='<tr'..style..'>'
    for i=1,spec.columns do out[#out+1]='<td'..alignment_attr(i)..'>'..render(cells[i] or '', i)..'</td>' end
    out[#out+1]='</tr>'
  end
  out[#out+1]='</tbody></table>'
  return pandoc.RawBlock('html', table.concat(out, '\n'))
end

local function make_area_table(spec)
  local area = ((spec.options or {}).area or 'text'):lower()
  local class = ({full='fullarea', half='halfarea', margin='marginarea',
                  directory='directoryarea'})[area]
  local table = make_table(spec)
  if class then return pandoc.Div({table}, pandoc.Attr('', {class}, {})) end
  return table
end

local function directory_block(kind)
  if kind == 'toc' then
    return pandoc.RawBlock('html', '<nav class="document-directory toc-directory" data-md-directory="toc"></nav>')
  end
  local title = kind == 'lof' and 'List of Figures' or 'List of Tables'
  local label = kind == 'lof' and 'Figure' or 'Table'
  local out = {'<nav class="document-directory '..kind..'-directory" aria-label="'..title..'">',
               '<h2 class="directory-title">'..title..'</h2>', '<ol class="directory-list">'}
  for _,entry in ipairs(((data.directories or {})[kind] or {})) do
    local source = (entry.caption or ''):gsub('\\mdlayout%s*{}', '\\MDWordmark')
      :gsub('\\mdlayout', '\\MDWordmark')
    local caption = pandoc.write(pandoc.Pandoc({pandoc.Plain(latex_inlines(source))}), 'html')
      :gsub('^%s*<p>',''):gsub('</p>%s*$',''):gsub('%s+$','')
    out[#out+1] = '<li><a href="#'..entry.label..'"><span class="directory-number">'
      ..label..' '..tostring(entry.number)..'</span><span class="directory-text">'
      ..caption..'</span></a></li>'
  end
  out[#out+1] = '</ol></nav>'
  return pandoc.RawBlock('html', table.concat(out, '\n'))
end

local function make_tabular(spec)
  local function esc(s)
    return (s:gsub('&','&amp;'):gsub('<','&lt;'):gsub('>','&gt;'):gsub('"','&quot;'))
  end
  local function render(raw)
    local delimiter, code = raw:match('^%s*\\verb(.)(.*)%s*$')
    if delimiter and code:sub(-1) == delimiter then
      return '<code>'..esc(code:sub(1,-2))..'</code>'
    end
    local html = pandoc.write(pandoc.Pandoc({pandoc.Plain(latex_inlines(raw))}), 'html')
    return html:gsub('^%s*<p>',''):gsub('</p>%s*$',''):gsub('%s+$','')
  end
  local out={'<div class="tabular-scroll"><table class="latex-tabular"><tbody>'}
  for _,row in ipairs(spec.rows or {}) do
    local cells, spacing = clean_table_row(row)
    local style = spacing and (' class="add-line-space" style="--md-row-space:'..spacing..'"') or ''
    out[#out+1]='<tr'..style..'>'
    for i=1,spec.columns do out[#out+1]='<td>'..render(cells[i] or '')..'</td>' end
    out[#out+1]='</tr>'
  end
  out[#out+1]='</tbody></table></div>'
  return pandoc.RawBlock('html', table.concat(out, '\n'))
end

function RawInline(el)
  local image = el.text:match('^\\MDImage{(%d+)}$')
  if image then return make_image(data.images[tonumber(image)+1]) end
  local see_right_scale = el.text:match('^\\MDSeeRight{([0-9.]+)}$')
  if see_right_scale then
    return see_right(see_right_scale)
  end
  local margin_note = el.text:match('^\\MDMarginPar{(.*)}$')
  if margin_note then
    return pandoc.Span(latex_inlines(margin_note),
      pandoc.Attr('', {'marginpar'}, {}))
  end
  local directory = el.text:match('^\\MDDirectory{([a-z]+)}$')
  if directory == 'toc' or directory == 'lof' or directory == 'lot' then
    return directory_block(directory)
  end
  if el.text:match('^\\MDWordmark%s*$') then
    local mark = make_wordmark()
    if el.text:match('%s+$') then return {mark, pandoc.Space()} end
    return mark
  end
  local syntax = el.text:match('^\\MDCodeInline{(%d+)}$')
  if syntax then return pandoc.Code(data.codeinlines[tonumber(syntax)+1] or '') end
  local latex_source = el.text:match('^\\MDLatexInline{(%d+)}$')
  if latex_source then
    return pandoc.Code(data.codeinlines[tonumber(latex_source)+1] or '',
      pandoc.Attr('', {'latex-fragment'}, {}))
  end
  local label = el.text:match('^\\MDLabel{([^}]+)}$')
  if label then return pandoc.RawInline('html', '<span id="'..label..'" class="latex-label"></span>') end
  local target, number = el.text:match('^\\MDRef{([^}]+)}{([^}]+)}$')
  if target then return pandoc.Link(number, '#'..target:gsub(' ', '%%20')) end
  local classlist, styled = el.text:match('^\\MDStyle{([^}]*)}{(.*)}$')
  if classlist then
    local classes = {}
    for class in classlist:gmatch('[^,]+') do classes[#classes+1]=class end
    return pandoc.Span(latex_inlines(styled), pandoc.Attr('', classes, {}))
  end
  local n = el.text:match('^\\MDCodeBlock{(%d+)}$')
  if n then return pandoc.Code(data.codeblocks[tonumber(n)+1] or '', {class='latex'}) end
  n = el.text:match('^\\MDPlainCodeBlock{(%d+)}$')
  if n then return pandoc.Code(data.codeblocks[tonumber(n)+1] or '') end
  n = el.text:match('^\\MDWideCodeBlock{(%d+)}$')
  if n then return pandoc.Code(data.codeblocks[tonumber(n)+1] or '') end
end

function Para(el)
  for _,inline in ipairs(el.content) do
    if inline.t == 'RawInline' then
      local tabular = inline.text:match('^\\MDTabular{(%d+)}$')
      if tabular then return make_tabular(data.tabulars[tonumber(tabular)+1]) end
      local table_class, direct_table = inline.text:match(
        '^\\MDStyledTable{([^}]*)}{(%d+)}$')
      if direct_table then
        return pandoc.Div({make_area_table(data.tables[tonumber(direct_table)+1])},
          pandoc.Attr('', {table_class}, {}))
      end
      local styled_classes, styled_table = inline.text:match(
        '^\\MDStyle{([^}]*)}{%s*\\MDReferenceTable{(%d+)}%s*}$')
      if styled_table then
        local classes = {}
        for class in styled_classes:gmatch('[^,]+') do classes[#classes+1]=class end
        return pandoc.Div({make_area_table(data.tables[tonumber(styled_table)+1])},
          pandoc.Attr('', classes, {}))
      end
      local code = inline.text:match('^\\MDCodeBlock{(%d+)}$')
      if code then
        return pandoc.CodeBlock(data.codeblocks[tonumber(code)+1] or '', {class='latex'})
      end
      code = inline.text:match('^\\MDPlainCodeBlock{(%d+)}$')
      if code then return pandoc.CodeBlock(data.codeblocks[tonumber(code)+1] or '') end
      code = inline.text:match('^\\MDWideCodeBlock{(%d+)}$')
      if code then
        return pandoc.Div(
          {pandoc.CodeBlock(data.codeblocks[tonumber(code)+1] or '')},
          pandoc.Attr('', {'fullarea', 'wideverbatim'}, {}))
      end
      code = inline.text:match('^\\MDListingCodeBlock{(%d+)}$')
      if code then return listing_block(tonumber(code)) end
      code = inline.text:match('^\\MDPrintoutCodeBlock{(%d+)}$')
      if code then return printout_block(tonumber(code)) end
      code = inline.text:match('^\\MDTextAreaCodeBlock{(%d+)}$')
      if code then
        return pandoc.Div(
          {pandoc.CodeBlock(data.codeblocks[tonumber(code)+1] or '')},
          pandoc.Attr('', {'textarea-content', 'verbatim-in-textarea'}, {}))
      end
      local n = inline.text:match('^\\MDReferenceTable{(%d+)}$')
      if n then return make_area_table(data.tables[tonumber(n)+1]) end
    end
  end
end

function RawBlock(el)
  local directory = el.text:match('^%s*\\MDDirectory{([a-z]+)}%s*$')
  if directory == 'toc' or directory == 'lof' or directory == 'lot' then
    return directory_block(directory)
  end
  local image = el.text:match('^%s*\\MDImage{(%d+)}%s*$')
  if image then return pandoc.Para({make_image(data.images[tonumber(image)+1])}) end
  local latex_source = el.text:match('^%s*\\MDLatexInline{(%d+)}%s*$')
  if latex_source then
    return pandoc.CodeBlock(data.codeinlines[tonumber(latex_source)+1] or '',
      pandoc.Attr('', {'latex-fragment'}, {}))
  end
  local inline_code = el.text:match('^%s*\\MDCodeInline{(%d+)}%s*$')
  if inline_code then
    return pandoc.Para({pandoc.Code(data.codeinlines[tonumber(inline_code)+1] or '')})
  end
  local tabular = el.text:match('^%s*\\MDTabular{(%d+)}%s*$')
  if tabular then return make_tabular(data.tabulars[tonumber(tabular)+1]) end
  local table_class, direct_table = el.text:match(
    '^%s*\\MDStyledTable{([^}]*)}{(%d+)}%s*$')
  if direct_table then
    return pandoc.Div({make_area_table(data.tables[tonumber(direct_table)+1])},
      pandoc.Attr('', {table_class}, {}))
  end
  local classlist, styled = el.text:match('^%s*\\MDStyle{([^}]*)}{(.*)}%s*$')
  if classlist then
    local classes = {}
    for class in classlist:gmatch('[^,]+') do classes[#classes+1]=class end
    return pandoc.Div(latex_blocks(styled), pandoc.Attr('', classes, {}))
  end
  local n = el.text:match('^%s*\\MDCodeBlock{(%d+)}%s*$')
  if n then return pandoc.CodeBlock(data.codeblocks[tonumber(n)+1] or '', {class='latex'}) end
  n = el.text:match('^%s*\\MDPlainCodeBlock{(%d+)}%s*$')
  if n then return pandoc.CodeBlock(data.codeblocks[tonumber(n)+1] or '') end
  n = el.text:match('^%s*\\MDWideCodeBlock{(%d+)}%s*$')
  if n then
    return pandoc.Div(
      {pandoc.CodeBlock(data.codeblocks[tonumber(n)+1] or '')},
      pandoc.Attr('', {'fullarea', 'wideverbatim'}, {}))
  end
  n = el.text:match('^%s*\\MDListingCodeBlock{(%d+)}%s*$')
  if n then return listing_block(tonumber(n)) end
  n = el.text:match('^%s*\\MDPrintoutCodeBlock{(%d+)}%s*$')
  if n then return printout_block(tonumber(n)) end
  n = el.text:match('^%s*\\MDTextAreaCodeBlock{(%d+)}%s*$')
  if n then
    return pandoc.Div(
      {pandoc.CodeBlock(data.codeblocks[tonumber(n)+1] or '')},
      pandoc.Attr('', {'textarea-content', 'verbatim-in-textarea'}, {}))
  end
  local multicol_count, multicol_body = el.text:match(
    '^%s*\\begin{multicols}%s*{(%d+)}%s*(.-)\\end{multicols}%s*$')
  if multicol_count then
    local count = math.max(1, math.min(8, tonumber(multicol_count) or 1))
    return pandoc.Div(
      latex_blocks(multicol_body),
      pandoc.Attr('', {'multicols'}, {{'style', '--md-columns:' .. count}}))
  end
  n = el.text:match('^%s*\\MDReferenceTable{(%d+)}%s*$')
  if n then return make_area_table(data.tables[tonumber(n)+1]) end
  local margin_body = el.text:match(
    '^%s*\\begin{MarginFigure}.-\n?(.*)\\end{MarginFigure}%s*$')
  if margin_body then
    margin_body = margin_body:gsub('^%s*%b[]%s*', '', 1)
    local caption_group = margin_body:match('\\caption%s*(%b{})')
    local caption = caption_group and caption_group:sub(2, -2) or nil
    local label = margin_body:match('\\MDLabel{([^}]+)}')
    if caption_group then margin_body = margin_body:gsub('\\caption%s*%b{}', '', 1) end
    local blocks = latex_blocks(margin_body)
    if caption then
      local caption_inlines = latex_inlines(caption)
      local reference = label and (data.refs or {})[label] or nil
      if reference and reference.number then
        table.insert(caption_inlines, 1, pandoc.Space())
        table.insert(caption_inlines, 1,
          pandoc.Span({pandoc.Str('Figure '..tostring(reference.number)..':')},
            pandoc.Attr('', {'figure-number'}, {})))
      end
      blocks[#blocks+1] = pandoc.Div(
        {pandoc.Para(caption_inlines)},
        pandoc.Attr('', {'marginfigure-caption'}, {}))
    end
    return pandoc.Div(blocks, pandoc.Attr('', {'marginfigure'}, {}))
  end
  for env,class in pairs(classes) do
    local pat = '^%s*\\begin{'..env..'}.-\n?(.*)\\end{'..env..'}%s*$'
    local body = el.text:match(pat)
    if body then
      -- Placement arguments such as [htbp] belong to LaTeX's float
      -- machinery and must never become visible HTML text.
      body = body:gsub('^%s*%b[]%s*', '', 1)
      return pandoc.Div(latex_blocks(body), {class=class})
    end
  end
end

function Image(el)
  -- Keep the alternative text when an image collection is unavailable.
  return el
end

function Math(el)
  -- \oiint comes from the LaTeX esint package and is not part of MathJax's
  -- default TeX command set.  Its Unicode substitute is optically much smaller
  -- than MathJax's integral glyphs, so give it a dedicated, tunable class.
  -- \nolimits retains integral-style subscript placement.
  el.text = el.text:gsub('\\oiiint', '{\\mathop{\\class{md-oiiint}{∰}}\\nolimits}')
                   :gsub('\\oiint',  '{\\mathop{\\class{md-oiint}{∯}}\\nolimits}')
  return el
end
