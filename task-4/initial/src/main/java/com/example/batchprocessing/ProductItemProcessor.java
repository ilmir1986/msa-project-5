package com.example.batchprocessing;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.springframework.batch.item.ItemProcessor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.DataClassRowMapper;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.util.concurrent.atomic.AtomicReference;

@Component
public class ProductItemProcessor implements ItemProcessor<Product, Product> {

	private static final Logger log = LoggerFactory.getLogger(ProductItemProcessor.class);

	@Autowired
	private JdbcTemplate jdbcTemplate;

    @Override
	public Product process(final Product product) {
		final Long productId = product.productId();
		final Long productSku = product.productSku();
		final String productName = product.productName();
		final Long productAmount = product.productAmount();
		final String productData = product.productData();

		AtomicReference<Product> transformedProduct = new AtomicReference<>(new Product(productId, productSku, productName, productAmount, productData));

		String sql = "SELECT * FROM loyality_data WHERE productSku=" + productSku ;
		jdbcTemplate.query(sql, new DataClassRowMapper<>(Loyality.class))
				.stream().findAny().map(Loyality::loyalityData).map(loyalityData -> {
                    return new Product(productId, productSku, productName, productAmount, loyalityData);
				}).map( p -> {
					transformedProduct.set(p);
                    return null;
                });

		log.info("Transforming ({}) into ({})", product, transformedProduct.get());

		return transformedProduct.get();
	}

}
