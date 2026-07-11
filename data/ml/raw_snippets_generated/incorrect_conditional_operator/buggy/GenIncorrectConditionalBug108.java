public class GenIncorrectConditionalBug108 {
    static void announce(int budget) {
        if (budget = 5) {
            System.out.println("hit the target");
        }
    }
}
