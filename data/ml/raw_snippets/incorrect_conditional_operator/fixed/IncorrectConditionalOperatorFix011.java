public class IncorrectConditionalFix011 {
    public void checkStatus(boolean status) {
        while (status == true) {
            System.out.println("Running");
            break;
        }
    }
}