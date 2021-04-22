"""Code used in ``tutorial-create.rst`` file."""
import resdk

res = resdk.Resolwe(url='https://app.genialis.com')
res.login()

# Get example reads
example = res.data.get('resdk-example-reads')
# Download them to current working directory
example.download(
    field_name='fastq',
    download_dir='./',
)

# Upload FASTQ reads
reads = res.run(
    slug='upload-fastq-single',
    input={
        'src': './reads.fastq.gz',
    }
)

reads.sample

# Change name
reads.name = 'My first data'
reads.save()

# define the chosen descriptor schema
reads.descriptor_schema = 'reads'

# define the descriptor
reads.descriptor = {
    'description': 'Some free text...',
}

# Very important: save changes!
reads.save()

reads.sample.descriptor_schema = 'sample'

reads.sample.descriptor = {
    'general': {
        'description': 'This is a sample...',
        'species': 'Homo sapiens',
        'strain': 'F1 hybrid FVB/N x 129S6/SvEv',
        'cell_type': 'glioblastoma',
    },
    'experiment': {
        'assay_type': 'rna-seq',
        'molecule': 'total_rna',
    },
}

reads.sample.save()

# create a new collection object in your running instance of Resolwe (res)
test_collection = res.collection.create(name='Test collection')



# add sample to collection
reads.sample.collection = test_collection
reads.sample.save()


# Get genome
genome_index = res.data.get('resdk-example-genome-index')

alignment = res.run(
    slug='alignment-star',
    input={
        'genome': genome_index,
        'reads': reads,
    },
)

# Get the latest meta data from the server
alignment.update()

# See the process progress
alignment.process_progress

# Print the status of data
alignment.status

# See process output
alignment.output

# Run a workflow
res.run(
    slug='workflow-bbduk-star-featurecounts-qc-single',
    input={
        'preprocessing': {'reads': reads},
        'alignment': {'genome': res.data.get('resdk-example-genome-index')},
        'quantification': {'annotation': res.data.get('resdk-example-annotation')},
        'qc': {
            'globin_reference': res.data.get('resdk-example-globin-index'),
            'rrna_reference': res.data.get('resdk-example-rrna-index'),
        },
    }
)

# Update the data object to get the most recent info
alignment.update()

# Print process' standard output
print(alignment.stdout())

# Access process' execution information
alignment.process_info

# Access process' execution warnings
alignment.process_warning

# Access process' execution errors
alignment.process_error
