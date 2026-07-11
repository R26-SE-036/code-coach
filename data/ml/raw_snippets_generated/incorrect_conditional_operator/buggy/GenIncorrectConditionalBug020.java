public class GenIncorrectConditionalBug020 {
    static void printAll1(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static void announce(int attempts) {
        if (attempts = 5) {
            System.out.println("hit the target");
        }
    }
}
