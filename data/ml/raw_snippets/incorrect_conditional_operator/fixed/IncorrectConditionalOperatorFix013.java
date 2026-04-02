public class IncorrectConditionalFix013 {
    public void validateUser(Object user) {
        if (user == null) {
            throw new IllegalArgumentException();
        }
    }
}