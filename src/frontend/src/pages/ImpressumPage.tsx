import React from "react";

const ImpressumPage: React.FC = () => {
  return (
    <div className="max-w-3xl mx-auto py-12 px-6">
      <h1 className="text-4xl font-black mb-8 dark:text-white text-gray-900 uppercase tracking-tight">Legal Notice (Impressum)</h1>
      
      <div className="space-y-8 dark:text-gray-400 text-gray-700">
        <section>
          <h2 className="text-xl font-bold dark:text-white text-gray-900 mb-2 uppercase tracking-widest">Information according to § 5 TMG</h2>
          <p>
            Example University Project<br />
            Computer Science Department<br />
            123 Knowledge Way<br />
            12345 Tech City
          </p>
        </section>

        <section>
          <h2 className="font-bold dark:text-white text-gray-900 mb-2 uppercase tracking-widest text-xs">Represented by</h2>
          <p>The PriceGoblin Team (John Doe, Jane Smith)</p>
        </section>

        <section>
          <h2 className="font-bold dark:text-white text-gray-900 mb-2 uppercase tracking-widest text-xs">Contact</h2>
          <p>
            Phone: +49 (0) 123 456789<br />
            Email: contact@pricegoblin.example.com
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold dark:text-white text-gray-900 mb-2 uppercase tracking-widest">Note</h2>
          <p>
            This website is a student project and does not provide professional services. All data is for educational purposes only.
          </p>
        </section>
      </div>
    </div>
  );
};

export default ImpressumPage;
