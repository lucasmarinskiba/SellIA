"use client";

import { useState } from "react";

interface FAQ {
  id: string;
  question: string;
  answer: string;
}

interface FAQAccordionProps {
  faqs: FAQ[];
}

export default function FAQAccordion({ faqs }: FAQAccordionProps) {
  const [openId, setOpenId] = useState<string | null>(null);

  if (faqs.length === 0) {
    return (
      <div className="text-center text-gray-400 text-sm py-8">
        No hay preguntas frecuentes disponibles.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {faqs.map((faq) => (
        <div key={faq.id} className="bg-white rounded-lg border shadow-sm">
          <button
            onClick={() => setOpenId(openId === faq.id ? null : faq.id)}
            className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition"
          >
            <span className="font-medium text-gray-800">{faq.question}</span>
            <span className="text-gray-400 text-lg">
              {openId === faq.id ? "−" : "+"}
            </span>
          </button>
          {openId === faq.id && (
            <div className="px-4 pb-4 text-sm text-gray-600 whitespace-pre-wrap">
              {faq.answer}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
