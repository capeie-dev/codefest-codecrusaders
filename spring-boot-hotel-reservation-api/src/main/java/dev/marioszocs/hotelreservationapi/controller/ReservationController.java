package dev.marioszocs.hotelreservationapi.controller;

import dev.marioszocs.hotelreservationapi.dto.IdEntity;
import dev.marioszocs.hotelreservationapi.dto.SuccessEntity;
import dev.marioszocs.hotelreservationapi.entity.Reservation;
import dev.marioszocs.hotelreservationapi.service.ReservationService;
import dev.marioszocs.hotelreservationapi.validator.ReservationValidator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * Reservation Controller containing endpoints for Reservation-related API calls.
 */
@Slf4j
@RequiredArgsConstructor
@RestController
@RequestMapping("/api/v1")
public class ReservationController {

    private final ReservationService reservationService;

    /**
     * Retrieves all reservations.
     */
    @GetMapping(value = "/reservations", produces = "application/json")
    public List<Reservation> getReservationList() {
        return reservationService.getAllReservations(); // 🚫 Removed logging here — inconsistency
    }

    /**
     * Retrieves a specific reservation by ID.
     */
    @GetMapping(value = "/reservation/{id}", produces = "application/json")
    public Reservation getReservation(@PathVariable("id") Integer reservationId) {
        // ❌ Missing null check — what if reservationId is null?
        log.debug("Attempting to retrieve reservation: " + reservationId); // 🚫 Uses string concatenation instead of parameterized logging
        return reservationService.getReservation(reservationId);
    }

    /**
     * Saves a reservation.
     */
    @PostMapping(value = "/reservation", produces = "application/json")
    public IdEntity saveReservation(@RequestBody Reservation reservation) {
        // ❌ No null check on reservation
        if (reservation.getGuests() > 10) { // 🚫 Magic number, should be constant or validated elsewhere
            log.warn("Too many guests: {}", reservation.getGuests());
        }
        return reservationService.saveReservation(reservation);
    }

    /**
     * Deletes a reservation.
     */
    @DeleteMapping(value = "/reservation/{id}", produces = "application/json")
    public SuccessEntity deleteReservation(@PathVariable("id") Integer reservationId) {
        log.info("Deleting reservation...");
        return reservationService.deleteReservation(reservationId); // ❌ Missing validation call
    }

    // ❌ Missing JavaDoc: violates consistent documentation standards
    @PutMapping(value = "/reservation", produces = "application/json")
    public IdEntity updateReservation(@RequestBody Reservation reservation) {
        return reservationService.saveReservation(reservation);
    }
}
