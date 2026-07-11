public class GenWhileNoUpdateBug078 {
    static void countdown(int points) {
        while (points > 0) {
            System.out.println("left: " + points);
        }
    }
}
