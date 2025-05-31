import React from 'react';

interface RecordingGuideProps {
  language?: 'en' | 'es';
}

export function RecordingGuide({ language = 'en' }: RecordingGuideProps) {
  const guides = {
    en: {
      title: "Recording Guide",
      intro: "For best results, structure your recording like this:",
      example: "Hi, I just finished a meeting with John Smith from TechCorp. John is the CTO there. We discussed their AI automation needs, specifically around workflow optimization. They're very interested in our platform and this is a high priority for them. John is a prospective client. For next steps, I need to send him a detailed proposal by Friday and schedule a technical demo with their engineering team next week.",
      tips: [
        "State the person's full name clearly",
        "Mention their company name",
        "Include their position or role",
        "Summarize what you discussed",
        "Specify if they're a new prospect or existing client",
        "Indicate priority level (high/medium/low)",
        "List specific action items"
      ]
    },
    es: {
      title: "Guía de Grabación",
      intro: "Para mejores resultados, estructura tu grabación así:",
      example: "Hola, acabo de terminar una reunión con María Rodríguez de GlobalTech. María es la Directora de Operaciones. Hablamos sobre sus necesidades de automatización de IA, específicamente la optimización de flujos de trabajo. Están muy interesados en nuestra plataforma y esto es de alta prioridad para ellos. María es un cliente prospectivo. Como próximos pasos, necesito enviarle una propuesta detallada para el viernes y programar una demostración técnica con su equipo de ingeniería la próxima semana.",
      tips: [
        "Indica el nombre completo de la persona claramente",
        "Menciona el nombre de su empresa",
        "Incluye su posición o rol",
        "Resume lo que discutieron",
        "Especifica si es un prospecto nuevo o cliente existente",
        "Indica el nivel de prioridad (alta/media/baja)",
        "Lista acciones específicas a seguir"
      ]
    }
  };

  const guide = guides[language];

  return (
    <div className="bg-terminal-cyan/10 rounded-lg p-4 text-sm space-y-3">
      <h4 className="text-terminal-cyan font-terminal text-base">{guide.title}</h4>
      
      <div>
        <p className="text-terminal-cyan/80 mb-2">{guide.intro}</p>
        <div className="bg-black/50 rounded p-3 italic text-terminal-cyan/70 text-xs">
          "{guide.example}"
        </div>
      </div>

      <div>
        <p className="text-terminal-cyan font-semibold mb-1">Key points to include:</p>
        <ul className="space-y-1">
          {guide.tips.map((tip, index) => (
            <li key={index} className="text-terminal-cyan/80 flex items-start">
              <span className="mr-2">•</span>
              <span>{tip}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}