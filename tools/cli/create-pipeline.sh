#!/bin/bash
# Pipeline Creation Tool

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <pipeline_name> [pipeline_title]"
    echo "Example: $0 my_new_pipeline 'My New Pipeline'"
    exit 1
fi

PIPELINE_NAME=$1
PIPELINE_TITLE=${2:-"${PIPELINE_NAME^}"}

echo "🚀 Creating new pipeline: $PIPELINE_NAME"

# Create pipeline directory
mkdir -p pipelines/$PIPELINE_NAME

# Copy template
cp -r pipelines/_templates/pipeline_template/* pipelines/$PIPELINE_NAME/

# Replace template variables
find pipelines/$PIPELINE_NAME -type f \( -name "*.yml" -o -name "*.yaml" -o -name "*.py" -o -name "*.sql" -o -name "*.md" \) \
    -exec sed -i "s/{{PIPELINE_NAME}}/$PIPELINE_NAME/g" {} \;
find pipelines/$PIPELINE_NAME -type f \( -name "*.yml" -o -name "*.yaml" -o -name "*.py" -o -name "*.sql" -o -name "*.md" \) \
    -exec sed -i "s/{{PIPELINE_TITLE}}/$PIPELINE_TITLE/g" {} \;

# Create initial data directories
mkdir -p pipelines/$PIPELINE_NAME/data/{raw,staging,processed,temp}

echo "✅ Pipeline '$PIPELINE_NAME' created successfully!"
echo ""
echo "Next steps:"
echo "1. Update pipelines/$PIPELINE_NAME/dbt/profiles.yml with correct database settings"
echo "2. Add your data models to pipelines/$PIPELINE_NAME/dbt/models/"
echo "3. Create orchestration code in pipelines/$PIPELINE_NAME/orchestration/"
echo "4. Update documentation in pipelines/$PIPELINE_NAME/docs/"
