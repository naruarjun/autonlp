from tensorflow import flags
import nltk
import re
import numpy as np
import generation.tensorflow_generate as gen_runner
import inference.inference as inf_runner
import os, shutil
import json

Flags=flags.FLAGS

def clean_str(string):
	string = string.strip().lower()

	string = re.sub(r"\s{2,}", " ", string)
	string = re.sub(r',', '', string)
	string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
	if 'let\'s' in string:
	    string = re.sub(r'let\'s', 'let us', string)
	if 'lets' in string:
	    string = re.sub(r'lets', 'let us', string)

	string = re.sub(r"\'s", " is", string)
	string = re.sub(r"\'ve", " have", string)
	if 'wont ' in string:
	    string = re.sub(r"won\'?t", "will not", string)
	if 'won\'t ' in string:
	    string = re.sub(r"won\'?t", "will not", string)

	if 'cant ' in string:
	    string = re.sub(r"n\'?t", " can not", string)
	if 'can\'t ' in string:
	    string = re.sub(r"n\'?t", " can not", string)

	string = re.sub(r"n\'t", " not", string)
	string = re.sub(r"\'re", " are", string)
	string = re.sub(r"\'d", " \'d", string)
	string = re.sub(r"\'ll", " will", string)
	string = re.sub(r",", " , ", string)
	string = re.sub(r"!", "", string)
	string = re.sub(r"\(", " \( ", string)
	string = re.sub(r"\)", " \) ", string)
	string = re.sub(r"\?", "", string)
	string = re.sub(r"\s{2,}", " ", string)
	# string = re.sub(r"\'", '', string)

	return string.strip()
def preprocess(sentence):
	sentence = sentence.lower()
	sentence=clean_str(sentence)

	tokenizer = nltk.RegexpTokenizer(r'\w+')

	tokens = tokenizer.tokenize(sentence)
	m=len(tokens)
	tokens=" ".join(tokens)
	return m,tokens
class Generation():

	def get_data(self):
		#this funtion assumes that data is present in a text file with each instance on seperate line
		#this function can be altered as required to get data from different files.
		#it returns the sentences as a list and the dictionary
		f=open(Flags.datafile,'r')
		text=f.read();

		sentence=text.split('\n')
		processed_sent=[]


		max=0
		for s in sentence:
			m,sent=preprocess(s)
			if m>max:
				max=m
			processed_sent.append(sent)
		dictionary={}
		dictionary['<start>']=0
		dictionary['<end>']=1
		for p in processed_sent:
			words=p.split()
			for w in words:
				if w not in dictionary:
					dictionary[w]=len(dictionary)
		return processed_sent,dictionary
	def run(self):
		data,dictionary=self.get_data()
		print('got data from '+str(Flags.datafile))

		try:
			os.mkdir(Flags.model_save_path)
			print('making directory '+str(Flags.model_save_path)+' to save models')
		except:
			print('saving model to '+str(Flags.model_save_path)+' directory')
			if Flags.restore_model==False:
				folder = Flags.model_save_path
				for the_file in os.listdir(folder):
					file_path = os.path.join(folder, the_file)
					try:
						if os.path.isfile(file_path):
						    os.unlink(file_path)
						elif os.path.isdir(file_path): shutil.rmtree(file_path)
					except Exception as e:
						pass
		 
		gen_runner.run(data,Flags.num_epochs,Flags.save_model_after_n_epochs,Flags.num_rnn_layers,Flags.learning_rate,Flags.rnn_block,Flags.num_units,Flags.fc1,Flags.fc2,len(dictionary),Flags.model_save_path,dictionary,len(data),Flags.device,Flags.max_seq_len_at_inference,Flags.glove_vector_location,testduringtrain=Flags.testduringtrain,keep_prob=Flags.keep_prob,restore=Flags.restore_model,minibatch_size=Flags.minibatch_size)

class Inference():
	def get_data(self):
		#this function is specific to SNLI dataset
		#this function can be altered as required to get data from different files.
		#it returns  sentences as two lists,labels and a dictionary
		f=open(Flags.datafile,'r')
		label=[]
		sentence1=[]
		sentence2=[]

		max1=0
		max2=0
		for line in f:
			json_line=json.loads(line)
			lab=json_line['annotator_labels']
			sent1=json_line['sentence1']
			sent2=json_line['sentence2']
			
			
			m1,sent1=preprocess(sent1)
			if max1<m1:
				max1=m1


			m2,sent2=preprocess(sent2)
			if max2<m2:
				max2=m2
			sentence1.append(sent1)
			sentence2.append(sent2)
			#print(lab[0])
			if str(lab[0]) == 'neutral':
				label.append(1)
			elif str(lab[0]) == 'contradiction':
				label.append(2)
			elif str(lab[0]) == 'entailment':
				label.append(0)	
		dictionary={}
		for p in sentence1:
			words=p.split()
			for w in words:
				if w not in dictionary:
					dictionary[w]=len(dictionary)	
		for p in sentence2:
			words=p.split()
			for w in words:
				if w not in dictionary:
					dictionary[w]=len(dictionary)			
		return sentence1,sentence2,max1,max2,dictionary,label
	def run(self):
		sentence1,sentence2,max1,max2,dictionary,label=self.get_data()
		print('got data from '+str(Flags.datafile))

		try:
			os.mkdir(Flags.model_save_path)
			print('making directory '+str(Flags.model_save_path)+' to save models')
		except:
			print('saving model to '+str(Flags.model_save_path)+' directory')
			if Flags.restore_model==False:
				folder = Flags.model_save_path
				for the_file in os.listdir(folder):
					file_path = os.path.join(folder, the_file)
					try:
						if os.path.isfile(file_path):
						    os.unlink(file_path)
						elif os.path.isdir(file_path): shutil.rmtree(file_path)
					except Exception as e:
						pass
			inf_runner.run(sentence1,sentence2,max1,max2,label,Flags.num_classes,Flags.num_epochs,Flags.save_model_after_n_epochs,Flags.num_rnn_layers,Flags.learning_rate,Flags.num_units,Flags.model_save_path,dictionary,Flags.device,Flags.glove_vector_location,len(dictionary),Flags.acc_file,Flags.loss_file,testduringtrain=Flags.testduringtrain,keep_prob=Flags.keep_prob,restore=Flags.restore_model,minibatch_size=Flags.inf_minibatch_size,trainingsetsize=Flags.inf_training_set_size)


if __name__=='__main__':
	flags.DEFINE_string("datafile",'snli_1.0/snli_1.0_train.jsonl','file which has the data')
	flags.DEFINE_string("task",'inference','can be generation or inference')
	flags.DEFINE_integer("num_epochs",10,'number of epochs')
	flags.DEFINE_integer('save_model_after_n_epochs',1,'number of epochs after which to save model')
	flags.DEFINE_string('model_save_path','generation/model','directory to save model')
	flags.DEFINE_bool('testduringtrain',True,'enable testing during training')
	flags.DEFINE_bool('restore_model',False,'True for restore model , False for starting new model')
	flags.DEFINE_string('device','/device:CPU:0','device to train the model on')
	flags.DEFINE_string('glove_vector_location','content/glove.6B.300d.txt','location of the pretrained glove vectors')
	###glove vectors can be obtained by executing the following commands
	###wget http://nlp.stanford.edu/data/glove.6B.zip 
	###unzip glove.6B.zip -d content


	#generation specific parameters
	
	flags.DEFINE_string("rnn_block",'LSTM','can be GRU or LSTM')
	flags.DEFINE_integer('num_units',32,'number of units in each lstm layer')
	flags.DEFINE_string("architecture of the block",'','can be uni-directional or bi-directional')
	flags.DEFINE_integer("num_rnn_layers",2,"number of layers in the recurrent neural network")
	flags.DEFINE_integer("fc1",128,'num units in first fc layer')
	flags.DEFINE_integer("fc2",256,'num units in second fc layer')
	flags.DEFINE_integer('minibatch_size',32,'batch size to use')
	flags.DEFINE_float('learning_rate',5e-4,'Learning rate for generation')
	flags.DEFINE_float('keep_prob',0.5,'dropout keep probability')	
	flags.DEFINE_integer('max_seq_len_at_inference',45,'set this to maximum length of an instance in your training set')
	
	
	#Natural language Inference specific parameters
	#The inference model is inspired by the following paper https://arxiv.org/pdf/1802.05577.pdf
	flags.DEFINE_integer('inf_num_rnn_layers',2,'number of layers in each bi-lstm')
	flags.DEFINE_integer('inf_num_rnn_units',256,'number of units in each lstm')
	flags.DEFINE_integer('inf_minibatch_size',32,'batch size for inference')
	flags.DEFINE_float('inf_learning_rate',5e-4,'learning rate for inference')
	flags.DEFINE_float('inf_dropout_keep_prob',0.5,'dropout for inference')
	flags.DEFINE_integer('inf_training_set_size',204800,'training set size during inference')
	flags.DEFINE_string('acc_file','inference/acc.pickle','file to store accuracy over epochs')
	flags.DEFINE_string('loss_file','inference/loss.pickle','file to store loss data over epochs')
	flags.DEFINE_integer('num_classes',3,'number of classes')


	if Flags.task is 'generation':
		g=Generation()
		g.run()
	elif Flags.task is 'inference':
		I=Inference()
		I.run()
