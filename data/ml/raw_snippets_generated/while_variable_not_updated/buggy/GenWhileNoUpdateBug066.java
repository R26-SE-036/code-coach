public class GenWhileNoUpdateBug066 {
    static void countdown(int steps) {
        while (steps > 0) {
            System.out.println("left: " + steps);
        }
    }
}
