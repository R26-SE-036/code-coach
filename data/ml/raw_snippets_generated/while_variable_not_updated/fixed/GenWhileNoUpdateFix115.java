public class GenWhileNoUpdateFix115 {
    static void countdown(int budget) {
        while (budget > 0) {
            System.out.println("left: " + budget);
            budget--;
        }
    }
}
