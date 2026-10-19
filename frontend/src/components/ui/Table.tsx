import React from "react";

export const Table: React.FC<React.TableHTMLAttributes<HTMLTableElement>> = ({
  className = "",
  children,
  ...props
}) => (
  <div className="table-wrapper">
    <table className={`table ${className}`.trim()} {...props}>
      {children}
    </table>
  </div>
);

export const Thead: React.FC<React.HTMLAttributes<HTMLTableSectionElement>> = ({
  className = "",
  children,
  ...props
}) => (
  <thead className={className} {...props}>
    {children}
  </thead>
);

export const Tbody: React.FC<React.HTMLAttributes<HTMLTableSectionElement>> = ({
  className = "",
  children,
  ...props
}) => (
  <tbody className={className} {...props}>
    {children}
  </tbody>
);

export interface TrProps extends React.HTMLAttributes<HTMLTableRowElement> {
  clickable?: boolean;
}

export const Tr: React.FC<TrProps> = ({
  clickable,
  className = "",
  children,
  ...props
}) => (
  <tr className={`${clickable ? "clickable" : ""} ${className}`.trim()} {...props}>
    {children}
  </tr>
);

export const Th: React.FC<React.ThHTMLAttributes<HTMLTableCellElement>> = ({
  className = "",
  children,
  ...props
}) => (
  <th className={className} {...props}>
    {children}
  </th>
);

export const Td: React.FC<React.TdHTMLAttributes<HTMLTableCellElement>> = ({
  className = "",
  children,
  ...props
}) => (
  <td className={className} {...props}>
    {children}
  </td>
);
