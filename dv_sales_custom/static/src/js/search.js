/** @odoo-module **/

import { Domain } from "@web/core/domain";
import { SearchModel } from "@web/search/search_model";
import {patch} from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { FACET_ICONS, FACET_COLORS } from "@web/search/utils/misc";

patch(SearchModel.prototype, {

    _getFieldDomain(field, autocompleteValues) {
        const domains = autocompleteValues.map(({ label, value, operator }) => {
            let domain;
            if (field.filterDomain) {
                domain = new Domain(field.filterDomain).toList({
                    self: label.trim(),
                    raw_value: value,
                });
            } else if (field.type === "field") {
                domain = [[field.fieldName, operator, value]];
            } else if (field.type === "field_property") {
                domain = [
                    field.propertyDomain,
                    [`${field.fieldName}.${field.propertyFieldDefinition.name}`, operator, value],
                ];
            }
            return new Domain(domain);
        });
        return Domain.and(domains); // Cambiar OR por AND
    },
    _getDomain(params = {}) {
        const withSearchPanel = "withSearchPanel" in params ? params.withSearchPanel : true;
        const withGlobal = "withGlobal" in params ? params.withGlobal : true;

        const groups = this._getGroups();
        const domains = [];
        if (withGlobal) {
            domains.push(this.globalDomain);
        }
        for (const group of groups) {
            const groupActiveItemDomains = [];
            for (const activeItem of group.activeItems) {
                const domain = this._getSearchItemDomain(activeItem);
                if (domain) {
                    groupActiveItemDomains.push(domain);
                }
            }
            const groupDomain = Domain.and(groupActiveItemDomains);
            domains.push(groupDomain);
        }

        // we need to manage (optional) facets, deactivateGroup, clearQuery,...

        if (this.display.searchPanel && withSearchPanel) {
            domains.push(this._getSearchPanelDomain());
        }

        let domain;
        try {
            domain = Domain.and(domains);
            return params.raw ? domain : domain.toList(this.domainEvalContext);
        } catch (error) {
            throw new Error(
                _t("Failed to evaluate the domain: %(domain)s.\n%(error)s", {
                    domain: domain.toString(),
                    error: error.message,
                })
            );
        }
    },
    _getFacets() {
        const facets = [];
        const groups = this._getGroups();
        for (const group of groups) {
            const groupActiveItemDomains = [];
            const values = [];
            let title;
            let type;
            for (const activeItem of group.activeItems) {
                const domain = this._getSearchItemDomain(activeItem, {
                    withDateFilterDomain: true,
                });
                if (domain) {
                    groupActiveItemDomains.push(domain);
                }
                const searchItem = this.searchItems[activeItem.searchItemId];
                switch (searchItem.type) {
                    case "field_property":
                    case "field": {
                        type = "field";
                        title = searchItem.description;
                        for (const autocompleteValue of activeItem.autocompletValues) {
                            values.push(autocompleteValue.label);
                        }
                        break;
                    }
                    case "groupBy": {
                        type = "groupBy";
                        values.push(searchItem.description);
                        break;
                    }
                    case "dateGroupBy": {
                        type = "groupBy";
                        for (const intervalId of activeItem.intervalIds) {
                            const option = this.intervalOptions.find((o) => o.id === intervalId);
                            values.push(`${searchItem.description}: ${option.description}`);
                        }
                        break;
                    }
                    case "dateFilter": {
                        type = "filter";
                        const periodDescription = this._getDateFilterDomain(
                            searchItem,
                            activeItem.generatorIds,
                            "description"
                        );
                        values.push(`${searchItem.description}: ${periodDescription}`);
                        break;
                    }
                    default: {
                        type = searchItem.type;
                        values.push(searchItem.description);
                    }
                }
            }
            const facet = {
                groupId: group.id,
                type,
                values,
                separator: type === "groupBy" ? ">" : _t("and"),
            };
            if (type === "field") {
                facet.title = title;
            } else {
                facet.icon = FACET_ICONS[type];
                facet.color = FACET_COLORS[type];
            }
            if (groupActiveItemDomains.length) {
                facet.domain = Domain.and(groupActiveItemDomains).toString();
            }
            facets.push(facet);
        }
 
        return facets;
    }
});