import { useEditor, EditorContent } from '@tiptap/react';
import Document from '@tiptap/extension-document';
import Paragraph from '@tiptap/extension-paragraph';
import Text from '@tiptap/extension-text';
import Bold from '@tiptap/extension-bold';
import History from '@tiptap/extension-history';
import './CantoEditor.css';

function linhasParaHtml(linhas) {
  return linhas
    .map((l) => {
      if (!l.texto.trim()) return '<p></p>';
      const escaped = l.texto.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      return l.negrito ? `<p><strong>${escaped}</strong></p>` : `<p>${escaped}</p>`;
    })
    .join('');
}

function htmlParaLinhas(html) {
  const div = document.createElement('div');
  div.innerHTML = html;
  const paragrafos = div.querySelectorAll('p');
  return Array.from(paragrafos).map((p) => {
    const texto = p.textContent || '';
    const negrito = p.querySelector('strong') !== null;
    return { texto, negrito };
  });
}

export default function CantoEditor({ titulo, linhas, onChange }) {
  const temNegrito = linhas.some((l) => l.negrito);

  const editor = useEditor({
    extensions: [Document, Paragraph, Text, Bold, History],
    content: linhasParaHtml(linhas),
    onUpdate({ editor }) {
      onChange(htmlParaLinhas(editor.getHTML()));
    },
  });

  if (!editor) return null;

  const toggleBold = () => editor.chain().focus().toggleBold().run();

  return (
    <div className={`canto-card ${temNegrito ? 'tem-refrao' : 'sem-refrao'}`}>
      <div className="canto-card-header">
        <span className="canto-titulo">{titulo}</span>
        <span className={`canto-badge ${temNegrito ? 'ok' : 'aviso'}`}>
          {temNegrito ? '✓ refrão' : '⚠ sem negrito'}
        </span>
      </div>

      <div className="canto-editor-toolbar">
        <button
          type="button"
          onClick={toggleBold}
          className={`toolbar-btn ${editor.isActive('bold') ? 'active' : ''}`}
          title="Negrito (Ctrl+B)"
        >
          <strong>N</strong>
        </button>
        <span className="toolbar-hint">Linha em branco = novo slide</span>
      </div>

      <EditorContent editor={editor} className="canto-editor-content" />
    </div>
  );
}
