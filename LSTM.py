import time
import matplotlib.pyplot as plt
import numpy as np
from numpy import newaxis
from keras.layers.core import Dense, Activation, Dropout
from keras.layers.recurrent import LSTM
from keras.models import Sequential

def load_data(filename, seq_len, normalise_window):
    f = open(filename, 'rb').read()
    data = f.split('\r\n')

    sequence_length = seq_len + 1
    result = []
    for index in range(len(data) - sequence_length):
        result.append(data[index: index + sequence_length])
    
    if normalise_window:
        result = normalise_windows(result)

    result = np.array(result)

    row = round(0.9 * result.shape[0])
    train = result[:row, :]
    np.random.shuffle(train)
    x_train = train[:, :-1]
    y_train = train[:, -1]
    x_test = result[row:, :-1]
    y_test = result[row:, -1]

    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))  

    return [x_train, y_train, x_test, y_test]

def normalise_windows(window_data):
    normalised_data = []
    for window in window_data:
        normalised_window = [((float(p) / float(window[0])) - 1) for p in window]
        normalised_data.append(normalised_window)
    return normalised_data

def build_model():
    model = Sequential()
    layers = [1, 50, 100, 1]

    model.add(LSTM(
        input_dim=layers[0],
        output_dim=layers[1],
        return_sequences=True))
    model.add(Dropout(0.2))

    model.add(LSTM(
        layers[2],
        return_sequences=False))
    model.add(Dropout(0.2))

    model.add(Dense(
        output_dim=layers[3]))
    model.add(Activation("linear"))

    start = time.time()
    model.compile(loss="mse", optimizer="rmsprop")
    print "Compilation Time : ", time.time() - start
    return model


def run_network():
    global_start_time = time.time()
    epochs  = 1
    seq_len = 50

    print 'Loading data... '
    X_train, y_train, X_test, y_test = load_data('sp500.csv', seq_len, True)
    print '\nData Loaded. Compiling...\n'

    model = build_model()

    try:
        model.fit(
            X_train,
            y_train,
            batch_size=512,
            nb_epoch=epochs,
            validation_split=0.05)

        #Shift the window by 1 new prediction each time, re-run predictions on new window
        curr_frame = X_test[0]
        predicted = []
        for i in xrange(len(X_test)):
            predicted.append(model.predict(curr_frame[newaxis,:,:])[0,0])
            curr_frame = curr_frame[1:]
            curr_frame = np.insert(curr_frame, [seq_len-1], predicted[-1], axis=0)
        
        '''
        #Predict each timestep given the last sequence of true data, in effect only predicting 1 step ahead each time
        predicted = model.predict(X_test)
        predicted = np.reshape(predicted, (predicted.size,))
        '''
    except KeyboardInterrupt:
        print 'Training duration (s) : ', time.time() - global_start_time
        return model, y_test, 0

    try:
        fig = plt.figure(facecolor='white')
        ax = fig.add_subplot(111)
        ax.plot(y_test, label='True Data')
        plt.plot(predicted, label='Prediction')
        plt.legend()
        plt.show()
    except Exception as e:
        print str(e)
    print 'Training duration (s) : ', time.time() - global_start_time
    
    return model, y_test, predicted

if __name__ == '__main__':
    run_network()