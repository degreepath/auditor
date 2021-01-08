use crate::ReportType;
use anyhow;
use dotenv::dotenv;
use openssl::ssl::{SslConnector, SslMethod, SslVerifyMode};
use postgres::{config::SslMode, Client, Config};
use postgres_openssl::MakeTlsConnector;

pub fn connect() -> anyhow::Result<Client> {
    dotenv().ok();

    let mut config = Config::new();
    config.user(&std::env::var("PGUSER").expect("PGUSER env var is required"));
    config.password(&std::env::var("PGPASSWORD").expect("PGPASSWORD env var is required"));
    config.host(&std::env::var("PGHOST").expect("PGHOST env var is required"));
    config.dbname(&std::env::var("PGDATABASE").expect("PGDATABASE env var is required"));
    config.application_name("degreepath-reports");
    config.ssl_mode(SslMode::Require);

    let mut connbuilder = SslConnector::builder(SslMethod::tls())?;
    connbuilder.set_verify(SslVerifyMode::NONE);
    let tls_connector_thing = MakeTlsConnector::new(connbuilder.build());

    let client = config.connect(tls_connector_thing)?;

    Ok(client)
}

pub fn record_report(
    client: &mut Client,
    report_type: &crate::ReportType,
    area_code: &str,
    content: &str,
) -> anyhow::Result<()> {
    let mut tx = client.transaction()?;

    let report_type_name = match report_type {
        ReportType::Report => "report",
        ReportType::Summary => "summary",
    };

    tx.execute(
        "
        INSERT INTO report (report_type, area_code, content, last_changed_at)
        VALUES ($1, $2, $3, current_timestamp)
        ON CONFLICT (report_type, area_code) DO UPDATE SET
              content = $3
            , last_changed_at = current_timestamp
    ",
        &[&report_type_name, &area_code, &content],
    )?;

    tx.commit()?;

    Ok(())
}

pub fn collect_area_codes(client: &mut Client) -> anyhow::Result<Vec<String>> {
    let mut tx = client.transaction()?;

    let results = tx.query(
        "
        SELECT DISTINCT area_code
        FROM result
        WHERE is_active = true
    ",
        &[],
    )?;

    let results = results
        .iter()
        .map(|record| record.get(0))
        .collect::<Vec<String>>();

    tx.commit()?;

    Ok(results)
}
