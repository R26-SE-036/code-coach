public class GenWhileNoUpdateFix024 {
    static void countdown(int steps) {
        while (steps > 0) {
            System.out.println("left: " + steps);
            steps--;
        }
    }
}
