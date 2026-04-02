public class IncorrectConditionalBug011 {
    public void checkStatus(boolean status) {
        while (status = true) {
            System.out.println("Running");
            break;
        }
    }
}