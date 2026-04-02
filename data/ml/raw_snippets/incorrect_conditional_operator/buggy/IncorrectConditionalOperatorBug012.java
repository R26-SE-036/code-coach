public class IncorrectConditionalBug012 {
    public void checkLength(int len) {
        if (len = 0) {
            return;
        }
    }
}