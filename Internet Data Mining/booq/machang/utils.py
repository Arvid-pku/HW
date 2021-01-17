# Save and Load Functions
import torch
import torch.nn as nn
def save_checkpoint(save_path, model, optimizer, valid_loss):
    if save_path == None:
        return

    state_dict = {'model_state_dict': model.state_dict(),
                  'optimizer_state_dict': optimizer.state_dict(),
                  'valid_loss': valid_loss}

    torch.save(state_dict, save_path)
    print(f'Model saved to ==> {save_path}')


def load_checkpoint(load_path, model, optimizer):
    if load_path == None:
        return

    state_dict = torch.load(load_path, map_location="cuda:0" if torch.cuda.is_available() else "cpu")
    print(f'Model loaded from <== {load_path}')

    model.load_state_dict(state_dict['model_state_dict'])
    optimizer.load_state_dict(state_dict['optimizer_state_dict'])

    return state_dict['valid_loss']


def save_metrics(save_path, train_loss_list, valid_loss_list, global_steps_list):
    if save_path == None:
        return

    state_dict = {'train_loss_list': train_loss_list,
                  'valid_loss_list': valid_loss_list,
                  'global_steps_list': global_steps_list}

    torch.save(state_dict, save_path)
    print(f'Model saved to ==> {save_path}')


def load_metrics(load_path):
    if load_path == None:
        return

    state_dict = torch.load(load_path, map_location="cuda:0" if torch.cuda.is_available() else "cpu")
    print(f'Model loaded from <== {load_path}')

    return state_dict['train_loss_list'], state_dict['valid_loss_list'], state_dict['global_steps_list']


# Training Function

def train(model,
          optimizer,
          train_loader,
          valid_loader,
           file_path ,#destination_folder,
            eval_every,
          criterion=nn.MSELoss(),
          num_epochs=5,
          best_valid_loss=float("Inf")):
    # initialize running values
    running_loss = 0.0
    valid_running_loss = 0.0
    correct =0
    valid_correct =0
    global_step = 0
    train_accuracy_list =[]
    valid_accuracy_list = []
    train_loss_list = []
    valid_loss_list = []
    global_steps_list = []
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    # training loop
    model.train()
    for epoch in range(num_epochs):
        for (text,label,textlen) in train_loader:
            text = text.long().to(device)
            label = label.float().to(device)
            textlen = textlen.to(device)
            output = model(text ,textlen)
            pred = torch.max(output, 1)[1]
            truth = torch.max(label, 1)[1]
            correct += (pred == truth).float().sum()
            loss = criterion(output, label)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # update running values
            running_loss += loss.item()
            global_step += 1

            # evaluation step
            if global_step % eval_every == 0:
                model.eval()
                with torch.no_grad():
                    # validation loop
                    for (text,label,textlen)in valid_loader:
                        text = text.long().to(device)
                        label = label.float().to(device)
                        textlen = textlen.to(device)
                        output = model(text, textlen)
                        pred = torch.max(output, 1)[1]
                        truth = torch.max(label, 1)[1]
                        valid_correct += (pred == truth).float().sum()
                        loss = criterion(output, label)
                        valid_running_loss += loss.item()

                # evaluation
                average_train_loss = running_loss / eval_every
                average_valid_loss = valid_running_loss / len(valid_loader)
                average_train_accuracy = correct/eval_every
                average_valid_accuracy = valid_correct/len(valid_loader)
                train_loss_list.append(average_train_loss)
                valid_loss_list.append(average_valid_loss)
                train_accuracy_list.append(average_train_accuracy)
                valid_accuracy_list.append(average_valid_accuracy)
                global_steps_list.append(global_step)

                # resetting running values
                running_loss = 0.0
                valid_running_loss = 0.0
                correct =0
                valid_correct = 0
                model.train()

                # print progress
                print('Epoch [{}/{}], Step [{}/{}], Train Accuracy: {:.4f}, Valid Accuracy: {:.4f},Train Loss: {:.4f}, Valid Loss: {:.4f}'
                      .format(epoch + 1, num_epochs, global_step, num_epochs * len(train_loader),average_train_accuracy,average_valid_accuracy,
                              average_train_loss, average_valid_loss))

                # checkpoint
                if best_valid_loss > average_valid_loss:
                    best_valid_loss = average_valid_loss
                    save_checkpoint(file_path + '/model.pt', model, optimizer, best_valid_loss)
                    save_metrics(file_path + '/metrics.pt', train_loss_list, valid_loss_list, global_steps_list)

    save_metrics(file_path + '/metrics.pt', train_loss_list, valid_loss_list, global_steps_list)
    print('Finished Training!')
    return train_accuracy_list,train_loss_list,valid_accuracy_list,valid_loss_list

def feature_train(model,
          optimizer,
          train_loader,
          valid_loader,
           file_path ,#destination_folder,
            eval_every,
          criterion=nn.BCELoss(),
          num_epochs=5,
          best_valid_loss=float("Inf")):
    # initialize running values
    running_loss = 0.0
    valid_running_loss = 0.0
    correct =0
    valid_correct =0
    global_step = 0
    train_accuracy_list =[]
    valid_accuracy_list = []
    train_loss_list = []
    valid_loss_list = []
    global_steps_list = []
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    # training loop
    model.train()
    for epoch in range(num_epochs):
        for (text,label) in train_loader:
            text = text.to(device)
            label = label.float().to(device)
            output = model(text)
            pred = torch.max(output, 1)[1]
            truth = torch.max(label, 1)[1]
            correct += (pred == truth).float().sum()
            loss = criterion(output, label)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # update running values
            running_loss += loss.item()
            global_step += 1

            # evaluation step
            if global_step % eval_every == 0:
                model.eval()
                with torch.no_grad():
                    # validation loop
                    for (text, label) in valid_loader:
                        text = text.to(device)
                        label = label.float().to(device)
                        output = model(text)
                        pred = torch.max(output, 1)[1]
                        truth = torch.max(label, 1)[1]
                        valid_correct += (pred == truth).float().sum()
                        loss = criterion(output, label)
                        valid_running_loss += loss.item()

                # evaluation
                average_train_loss = running_loss / eval_every
                average_valid_loss = valid_running_loss / len(valid_loader)
                average_train_accuracy = correct/100000
                average_valid_accuracy = valid_correct/10000
                train_loss_list.append(average_train_loss)
                valid_loss_list.append(average_valid_loss)
                train_accuracy_list.append(average_train_accuracy)
                valid_accuracy_list.append(average_valid_accuracy)
                global_steps_list.append(global_step)

                # resetting running values
                running_loss = 0.0
                valid_running_loss = 0.0
                correct =0
                valid_correct = 0
                model.train()

                # print progress
                print('Epoch [{}/{}], Step [{}/{}], Train Accuracy: {:.4f}, Valid Accuracy: {:.4f},Train Loss: {:.4f}, Valid Loss: {:.4f}'
                      .format(epoch + 1, num_epochs, global_step, num_epochs * len(train_loader),average_train_accuracy,average_valid_accuracy,
                              average_train_loss, average_valid_loss))

                # checkpoint
                if best_valid_loss > average_valid_loss:
                    best_valid_loss = average_valid_loss
                    save_checkpoint(file_path + '/model.pt', model, optimizer, best_valid_loss)
                    save_metrics(file_path + '/metrics.pt', train_loss_list, valid_loss_list, global_steps_list)

    save_metrics(file_path + '/metrics.pt', train_loss_list, valid_loss_list, global_steps_list)
    print('Finished Training!')
    return train_accuracy_list,train_loss_list,valid_accuracy_list,valid_loss_list

def siamese_train(model,
          optimizer,
          train_loader,
          valid_loader,
           file_path ,#destination_folder,
            eval_every,
          criterion=nn.MSELoss(),
          num_epochs=5,
          best_valid_loss=float("Inf")):
    # initialize running values
    running_loss = 0.0
    valid_running_loss = 0.0
    correct =0
    valid_correct =0
    global_step = 0
    train_accuracy_list =[]
    valid_accuracy_list = []
    train_loss_list = []
    valid_loss_list = []
    global_steps_list = []
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    # training loop
    model.train()
    for epoch in range(num_epochs):
        for (question,passage,label,question_len,passage_len) in train_loader:
            question= question.long().to(device)
            passage = passage.long().to(device)
            label = label.float().to(device)
            # question_len = question_len.to(device)
            # passage_len = passage_len.to(device)
            output = model(question,passage ,question_len,passage_len)
            pred = torch.max(output, 1)[1]
            truth = torch.max(label, 1)[1]
            correct += (pred == truth).float().sum()
            loss = criterion(output, label)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # update running values
            running_loss += loss.item()
            global_step += 1

            # evaluation step
            if global_step % eval_every == 0:
                model.eval()
                with torch.no_grad():
                    # validation loop
                    for (question, passage, label, question_len, passage_len) in valid_loader:
                        question = question.long().to(device)
                        passage = passage.long().to(device)
                        label = label.float().to(device)
                        # question_len = question_len.to(device)
                        # passage_len = passage_len.to(device)
                        output = model(question, passage, question_len, passage_len)
                        pred = torch.max(output, 1)[1]
                        truth = torch.max(label, 1)[1]
                        valid_correct += (pred == truth).float().sum()
                        loss = criterion(output, label)
                        valid_running_loss += loss.item()

                # evaluation
                average_train_loss = running_loss / eval_every
                average_valid_loss = valid_running_loss / len(valid_loader)
                average_train_accuracy = correct/eval_every
                average_valid_accuracy = valid_correct/len(valid_loader)
                train_loss_list.append(average_train_loss)
                valid_loss_list.append(average_valid_loss)
                train_accuracy_list.append(average_train_accuracy)
                valid_accuracy_list.append(average_valid_accuracy)
                global_steps_list.append(global_step)

                # resetting running values
                running_loss = 0.0
                valid_running_loss = 0.0
                correct =0
                valid_correct = 0
                model.train()

                # print progress
                print('Epoch [{}/{}], Step [{}/{}], Train Accuracy: {:.4f}, Valid Accuracy: {:.4f},Train Loss: {:.4f}, Valid Loss: {:.4f}'
                      .format(epoch + 1, num_epochs, global_step, num_epochs * len(train_loader),average_train_accuracy,average_valid_accuracy,
                              average_train_loss, average_valid_loss))

                # checkpoint
                if best_valid_loss > average_valid_loss:
                    best_valid_loss = average_valid_loss
                    save_checkpoint(file_path + '/model.pt', model, optimizer, best_valid_loss)
                    save_metrics(file_path + '/metrics.pt', train_loss_list, valid_loss_list, global_steps_list)

    save_metrics(file_path + '/metrics.pt', train_loss_list, valid_loss_list, global_steps_list)
    print('Finished Training!')
    return train_accuracy_list,train_loss_list,valid_accuracy_list,valid_loss_list
