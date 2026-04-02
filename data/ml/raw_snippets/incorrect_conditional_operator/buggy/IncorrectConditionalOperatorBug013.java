public class IncorrectConditionalBug013 {
    public void validateUser(Object user) {
        if (user = null) {
            throw new IllegalArgumentException();
        }
    }
}