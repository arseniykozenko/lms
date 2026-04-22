import React from "react";
import { Breadcrumb } from "antd";
import { Link } from "react-router-dom";

export function PageBreadcrumbs({ items }) {
  const normalizedItems = items.map((item) => ({
    title: item.href ? <Link to={item.href}>{item.label}</Link> : item.label,
  }));

  return <Breadcrumb className="page-breadcrumb" items={normalizedItems} />;
}
