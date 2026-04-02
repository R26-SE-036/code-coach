public class IncorrectConditionalBug015 {
    public void parseVal(int val) {
        int z = (val = 5) ? 1 : 0;
    }
}