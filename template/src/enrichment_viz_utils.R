#' Enrichment Visualization Utilities
#'
#' Shared visualization functions for PTMSEA, KinaseLibrary GSEA, and MEA analyses.
#' These functions provide consistent plotting styles across enrichment analyses.

library(ggplot2)
library(dplyr)
library(forcats)

#' Prepare enrichment data with common computed columns
#'
#' Adds neg_log_fdr, direction, and significant columns to enrichment results.
#' This is a shared helper used by plot functions and analyses.
#'
#' @param data Data frame with NES and FDR columns
#' @param fdr_col Name of FDR column (default: "FDR")
#' @param fdr_threshold FDR threshold for significance (default: 0.1)
#' @return Data frame with added neg_log_fdr, direction, significant columns
prepare_enrichment_data <- function(data, fdr_col = "FDR", fdr_threshold = 0.1) {
  data |>
    dplyr::mutate(
      neg_log_fdr = -log10(pmax(.data[[fdr_col]], 1e-10)),
      direction = dplyr::case_when(
        NES > 0 ~ "Up",
        NES < 0 ~ "Down",
        TRUE ~ "NS"
      ),
      significant = .data[[fdr_col]] < fdr_threshold
    )
}

#' Create enrichment dotplot for top items by FDR
#'
#' @param data Data frame with columns: item (kinase/pathway), NES, p.adjust/FDR, contrast
#' @param item_col Name of item column (default: "kinase")
#' @param fdr_col Name of FDR column (default: "FDR")
#' @param n_top Number of top items to show (default: 30)
#' @param title Plot title
#' @param subtitle Plot subtitle
#' @return ggplot object
plot_enrichment_dotplot <- function(data, item_col = "kinase", fdr_col = "FDR",
                                     n_top = 30, title = NULL, subtitle = "Top 30 by FDR") {
  # Prepare data using shared helper
  plot_data <- prepare_enrichment_data(data, fdr_col, 0.1) |>
    arrange(.data[[fdr_col]]) |>
    head(n_top) |>
    mutate(item = fct_reorder(.data[[item_col]], NES))

  ggplot(plot_data, aes(x = NES, y = item)) +
    geom_point(aes(size = neg_log_fdr, color = NES, alpha = significant)) +
    scale_color_gradient2(low = "blue", mid = "grey80", high = "red", midpoint = 0) +
    scale_size_continuous(name = "-log10(FDR)", range = c(2, 8)) +
    scale_alpha_manual(values = c("TRUE" = 1, "FALSE" = 0.4), guide = "none") +
    geom_vline(xintercept = 0, linetype = "dashed", color = "grey50") +
    theme_bw() +
    theme(axis.text.y = element_text(size = 9)) +
    labs(
      title = title,
      subtitle = subtitle,
      x = "Normalized Enrichment Score (NES)",
      y = ""
    )
}


#' Create volcano plot for enrichment results
#'
#' @param data Data frame with columns: NES, p.adjust/FDR, contrast, item (kinase/pathway)
#' @param item_col Name of item column for labels (default: "kinase")
#' @param fdr_col Name of FDR column (default: "FDR")
#' @param fdr_threshold FDR threshold for significance line (default: 0.1)
#' @param label_fdr_threshold FDR threshold for labeling points (default: 0.05)
#' @param n_labels Number of top labels per contrast (default: 5)
#' @param title Plot title
#' @param subtitle Plot subtitle
#' @return ggplot object
plot_enrichment_volcano <- function(data, item_col = "kinase", fdr_col = "FDR",
                                     fdr_threshold = 0.1, label_fdr_threshold = 0.05,
                                     n_labels = 5, title = NULL, subtitle = NULL) {
  # Prepare data using shared helper
  volcano_data <- prepare_enrichment_data(data, fdr_col, fdr_threshold)

  # Default subtitle
  if (is.null(subtitle)) {
    subtitle <- paste0("Dashed line: FDR = ", fdr_threshold, "; Labels: top ", n_labels, " by FDR per contrast")
  }

  ggplot(volcano_data, aes(x = NES, y = neg_log_fdr)) +
    geom_point(aes(color = direction, alpha = significant), size = 2) +
    geom_hline(yintercept = -log10(fdr_threshold), linetype = "dashed", color = "grey30") +
    geom_vline(xintercept = 0, linetype = "dashed", color = "grey30") +
    geom_text(
      data = volcano_data |>
        filter(.data[[fdr_col]] < label_fdr_threshold) |>
        group_by(contrast) |>
        slice_min(.data[[fdr_col]], n = n_labels),
      aes(label = .data[[item_col]]),
      size = 2.5,
      hjust = -0.1,
      check_overlap = TRUE
    ) +
    scale_color_manual(values = c("Up" = "red", "Down" = "blue", "NS" = "grey50")) +
    scale_alpha_manual(values = c("TRUE" = 1, "FALSE" = 0.3), guide = "none") +
    facet_wrap(~contrast, scales = "free") +
    theme_bw() +
    labs(
      title = title,
      subtitle = subtitle,
      x = "NES",
      y = "-log10(FDR)",
      color = "Direction"
    )
}


#' Create NES heatmap for top items across contrasts
#'
#' @param data Data frame with columns: item (ID/kinase), NES, p.adjust/FDR, contrast
#' @param item_col Name of item column (default: "ID")
#' @param fdr_col Name of FDR column (default: "p.adjust")
#' @param fdr_filter FDR threshold for selecting top items (default: 0.15)
#' @param n_top Number of top items to show (default: 25)
#' @param item_label_col Optional column for shorter labels (default: NULL, uses item_col)
#' @param title Plot title
#' @param subtitle Plot subtitle
#' @return ggplot object
plot_enrichment_heatmap <- function(data, item_col = "ID", fdr_col = "p.adjust",
                                     fdr_filter = 0.15, n_top = 25,
                                     item_label_col = NULL, title = NULL, subtitle = NULL) {
  # Find top items across all contrasts

  top_items <- data |>
    filter(.data[[fdr_col]] < fdr_filter) |>
    group_by(.data[[item_col]]) |>
    summarize(min_padj = min(.data[[fdr_col]]), .groups = "drop") |>
    arrange(min_padj) |>
    head(n_top) |>
    pull(.data[[item_col]])

  # Use item_col for labels if no separate label column provided
  if (is.null(item_label_col)) {
    item_label_col <- item_col
  }

  # Prepare heatmap data

heatmap_data <- data |>
    filter(.data[[item_col]] %in% top_items) |>
    mutate(
      item_label = .data[[item_label_col]],
      sig_label = case_when(
        .data[[fdr_col]] < 0.01 ~ "***",
        .data[[fdr_col]] < 0.05 ~ "**",
        .data[[fdr_col]] < 0.1 ~ "*",
        TRUE ~ ""
      )
    )

  # Default subtitle
  if (is.null(subtitle)) {
    subtitle <- "Top items (* p<0.1, ** p<0.05, *** p<0.01)"
  }

  ggplot(heatmap_data, aes(x = contrast, y = reorder(item_label, NES), fill = NES)) +
    geom_tile(color = "white") +
    geom_text(aes(label = sig_label), color = "black", size = 4) +
    scale_fill_gradient2(low = "blue", mid = "white", high = "red", midpoint = 0) +
    theme_minimal() +
    theme(
      axis.text.x = element_text(angle = 45, hjust = 1, size = 9),
      axis.text.y = element_text(size = 9)
    ) +
    labs(
      title = title,
      subtitle = subtitle,
      x = "", y = "", fill = "NES"
    )
}


#' Export GSEA enrichment plots to PDF
#'
#' @param results Named list of clusterProfiler GSEA result objects
#' @param output_file Path to output PDF file
#' @param fdr_threshold FDR threshold for including plots (default: 0.25)
#' @param width PDF width in inches (default: 10)
#' @param height PDF height in inches (default: 6)
#' @param prefix_pattern Regex pattern to strip from pathway names for titles (default: NULL)
#' @return Number of plots exported
export_gsea_plots_pdf <- function(results, output_file, fdr_threshold = 0.25,
                                   width = 10, height = 6, prefix_pattern = NULL) {
  pdf(output_file, width = width, height = height)

  n_plots <- 0
  for (ct in names(results)) {
    res <- results[[ct]]
    genesets <- res@result |>
      as_tibble() |>
      filter(p.adjust < fdr_threshold) |>
      arrange(pvalue) |>
      pull(ID)

    for (geneset in genesets) {
      row <- res@result |> as_tibble() |> filter(ID == geneset)

      # Clean pathway name for title
      pathway_label <- geneset
      if (!is.null(prefix_pattern)) {
        pathway_label <- gsub(prefix_pattern, "", geneset)
      }

      nes_val <- round(row$NES, 2)
      fdr <- signif(row$p.adjust, 2)

      p <- enrichplot::gseaplot2(res, geneSetID = geneset,
        title = paste0(ct, ": ", pathway_label, " (NES=", nes_val, ", FDR=", fdr, ")"))
      print(p)
      n_plots <- n_plots + 1
    }
  }

  dev.off()
  return(n_plots)
}


#' Create summary table for enrichment results
#'
#' @param results Named list of clusterProfiler GSEA result objects OR data frame
#' @param fdr_thresholds Vector of FDR thresholds to count (default: c(0.1, 0.05))
#' @return tibble with summary statistics
summarize_enrichment_results <- function(results, fdr_thresholds = c(0.1, 0.05)) {
  if (is.data.frame(results)) {
    # Handle data frame input (MEA style)
    results |>
      group_by(contrast) |>
      summarize(
        total = n(),
        `FDR < 0.1` = sum(FDR < 0.1, na.rm = TRUE),
        `FDR < 0.05` = sum(FDR < 0.05, na.rm = TRUE),
        .groups = "drop"
      )
  } else {
    # Handle clusterProfiler results list
    tibble(
      Contrast = names(results),
      `Total` = map_int(results, ~nrow(.x@result)),
      `FDR < 0.1` = map_int(results, ~sum(.x@result$p.adjust < 0.1, na.rm = TRUE)),
      `FDR < 0.05` = map_int(results, ~sum(.x@result$p.adjust < 0.05, na.rm = TRUE))
    )
  }
}


#' Prepare results data frame from clusterProfiler GSEA results
#'
#' @param results Named list of clusterProfiler GSEA result objects
#' @return tibble with all results combined
extract_gsea_results <- function(results) {
  names(results) |>
    purrr::map_dfr(function(ct) {
      res <- results[[ct]]@result
      tibble(
        ID = as.character(res[["ID"]]),
        NES = as.numeric(res[["NES"]]),
        pvalue = as.numeric(res[["pvalue"]]),
        p.adjust = as.numeric(res[["p.adjust"]]),
        setSize = as.integer(res[["setSize"]]),
        contrast = ct
      )
    })
}
